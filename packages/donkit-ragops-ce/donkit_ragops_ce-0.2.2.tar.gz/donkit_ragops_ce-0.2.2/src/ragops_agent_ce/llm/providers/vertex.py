from __future__ import annotations

import json
import os

# Google Gen AI SDK
from google import genai
from google.genai import types
from google.oauth2 import service_account
from loguru import logger

from ...config import Settings, load_settings
from ...logging_config import setup_logging
from ..base import LLMProvider
from ..types import LLMResponse, Message, ToolCall, ToolFunctionCall, ToolSpec


class VertexProvider(LLMProvider):
    name: str = "vertex"

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        credentials_data: dict[str, str] | None = None,
        model_name: str | None = None,
    ) -> None:
        self.settings = settings or load_settings()
        # Ensure logging is configured according to .env / settings
        try:
            setup_logging(self.settings)
        except Exception:
            pass

        if not credentials_data:
            raise ValueError("Vertex credentials are not set")

        service_account.Credentials.from_service_account_info(
            credentials_data, scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        # Set up environment for Vertex AI
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/vertex_creds.json"
        with open("/tmp/vertex_creds.json", "w") as f:
            json.dump(credentials_data, f)
        # Create client for Vertex AI
        self._client = genai.Client(
            # TODO: move proj and loc to settings before release
            vertexai=True,
            project=credentials_data.get("project_id"),
            location="us-central1",
        )

        self._model_name = model_name or self.settings.llm_model or "gemini-2.5-flash"

    @staticmethod
    def _clean_json_schema(schema: dict | None) -> types.Schema:
        """
        Transform an arbitrary JSON Schema-like dict (possibly produced by Pydantic)
        into a google.genai.types.Schema instance by:
        - Inlining $ref by replacing references with actual schemas from $defs
        - Removing $defs after inlining all references
        - Renaming unsupported keys to the SDK's expected snake_case
        - Recursively converting nested schemas (properties, items, anyOf)
        - Preserving fields supported by the SDK Schema model
        """
        if not isinstance(schema, dict):
            # Fallback to an object schema when input is not a dict
            return types.Schema()

        # Step 1: Inline $ref references before any conversion
        defs = schema.get("$defs", {})

        def inline_refs(obj, definitions):
            """Recursively inline $ref references."""
            if isinstance(obj, dict):
                # If this object has a $ref, replace it with the referenced schema
                if "$ref" in obj:
                    ref_path = obj["$ref"]
                    if ref_path.startswith("#/$defs/"):
                        ref_name = ref_path.replace("#/$defs/", "")
                        if ref_name in definitions:
                            # Get the referenced schema and inline it recursively
                            referenced = definitions[ref_name].copy()
                            # Preserve description and default from the referencing object
                            if "description" in obj and "description" not in referenced:
                                referenced["description"] = obj["description"]
                            if "default" in obj:
                                referenced["default"] = obj["default"]
                            return inline_refs(referenced, definitions)
                    # If can't resolve, remove the $ref
                    return {k: v for k, v in obj.items() if k != "$ref"}

                # Recursively process all properties
                result = {}
                for key, value in obj.items():
                    if key == "$defs":
                        continue  # Remove $defs after inlining
                    # Skip additionalProperties: true as it's not well supported
                    if key == "additionalProperties" and value is True:
                        continue
                    result[key] = inline_refs(value, definitions)
                return result
            elif isinstance(obj, list):
                return [inline_refs(item, definitions) for item in obj]
            else:
                return obj

        # Inline all references
        schema = inline_refs(schema, defs)

        # Debug: Log the inlined schema

        # Step 2: Convert to SDK schema format
        # Mapping from common JSON Schema/OpenAPI keys to google-genai Schema fields
        key_map = {
            "anyOf": "any_of",
            "additionalProperties": "additional_properties",
            "maxItems": "max_items",
            "maxLength": "max_length",
            "maxProperties": "max_properties",
            "minItems": "min_items",
            "minLength": "min_length",
            "minProperties": "min_properties",
            "propertyOrdering": "property_ordering",
        }

        def convert(obj):
            if isinstance(obj, dict):
                out: dict[str, object] = {}
                for k, v in obj.items():
                    kk = key_map.get(k, k)
                    if kk == "properties" and isinstance(v, dict):
                        # properties: dict[str, Schema]
                        out[kk] = {pk: convert(pv) for pk, pv in v.items()}
                    elif kk == "items":
                        # items: Schema (treat list as first item schema)
                        if isinstance(v, list) and v:
                            out[kk] = convert(v[0])
                        else:
                            out[kk] = convert(v)
                    elif kk == "any_of" and isinstance(v, list):
                        out[kk] = [convert(iv) for iv in v]
                    else:
                        out[kk] = convert(v)
                return out
            elif isinstance(obj, list):
                return [convert(i) for i in obj]
            else:
                return obj

        converted = convert(schema)

        # Debug: Log the converted schema

        try:
            result = types.Schema(**converted)  # type: ignore[arg-type]
            return result
        except Exception as e:
            logger.error(
                f"Failed to construct types.Schema from converted schema: {e}. "
                f"Schema was: {json.dumps(converted, default=str, indent=2)}"
            )
            return types.Schema()

    def generate(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        tools: list[ToolSpec] | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> LLMResponse:
        def _safe_text(text: str) -> str:
            try:
                return text.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
            except Exception:
                return ""

        contents: list[types.Content] = []
        system_instruction = ""

        # Group consecutive tool messages into single Content
        i = 0
        while i < len(messages):
            m = messages[i]

            if m.role == "tool":
                # Collect all consecutive tool messages
                tool_parts = []
                while i < len(messages) and messages[i].role == "tool":
                    tool_msg = messages[i]
                    part = types.Part.from_function_response(
                        name=tool_msg.name or "",
                        response={"result": _safe_text(tool_msg.content or "")},
                    )
                    tool_parts.append(part)
                    i += 1
                # Add all tool responses as a single Content
                if tool_parts:
                    contents.append(types.Content(role="tool", parts=tool_parts))
                continue
            elif m.role == "system":
                system_instruction += _safe_text(m.content).strip()
                i += 1
            elif m.role == "assistant":
                if m.tool_calls:
                    # Assistant message with tool calls
                    parts_list = []
                    for tc in m.tool_calls:
                        if not tc.function.name:
                            logger.warning("Skipping tool call without name in history")
                            continue
                        args = (
                            tc.function.arguments if isinstance(tc.function.arguments, dict) else {}
                        )
                        part = types.Part.from_function_call(name=tc.function.name, args=args)
                        parts_list.append(part)
                    if parts_list:
                        contents.append(types.Content(role="assistant", parts=parts_list))
                elif m.content:
                    # Regular assistant text response
                    part = types.Part(text=_safe_text(m.content))
                    contents.append(types.Content(role="assistant", parts=[part]))
                # Skip empty assistant messages without tool_calls or content
                i += 1
            else:
                part = types.Part(text=_safe_text(m.content))
                contents.append(types.Content(role=m.role, parts=[part]))
                i += 1
        config = types.GenerateContentConfig(
            temperature=temperature if temperature is not None else 0.2,
            top_p=top_p if top_p is not None else 0.95,
            max_output_tokens=max_tokens if max_tokens is not None else 8192,
            system_instruction=system_instruction if system_instruction else None,
        )
        if tools:
            function_declarations: list[types.FunctionDeclaration] = []
            for t in tools:
                schema_obj = self._clean_json_schema(t.function.parameters or {})
                function_declarations.append(
                    types.FunctionDeclaration(
                        name=t.function.name,
                        description=t.function.description or "",
                        parameters=schema_obj,
                    )
                )
            gen_tools = [types.Tool(function_declarations=function_declarations)]
            config.tools = gen_tools

        model_name = model or self._model_name

        try:
            response = self._client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
            text, tool_calls = self._parse_response(response)
            raw = response.model_dump()
            return LLMResponse(content=text, tool_calls=tool_calls, raw=raw)
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return LLMResponse(content="")

    @staticmethod
    def _parse_response(response) -> tuple[str | None, list[ToolCall] | None]:
        """Parse a genai response (or stream chunk) into plain text and tool calls."""
        text = ""
        calls: list[ToolCall] = []

        try:
            cand_list = response.candidates
        except AttributeError:
            cand_list = None
        if not cand_list:
            return None, None

        cand = cand_list[0]

        # Log finish reason if response was cut off
        try:
            finish_reason = cand.finish_reason
            if finish_reason and finish_reason != "STOP":
                logger.warning(f"Response finished with reason: {finish_reason}")
        except AttributeError:
            pass

        try:
            parts = cand.content.parts or []
        except AttributeError:
            parts = []

        # Collect text directly
        collected_text: list[str] = []
        for p in parts:
            try:
                t = p.text
            except AttributeError:
                t = ""
            if t:
                collected_text.append(t)
        text = "".join(collected_text)

        # Collect tool calls directly
        for p in parts:
            try:
                fc = p.function_call
            except AttributeError:
                fc = None
            if not fc:
                continue
            args = {}
            try:
                if fc.args:
                    args = dict(fc.args) if isinstance(fc.args, dict) else dict(fc.args)
            except AttributeError:
                args = {}
            try:
                name = fc.name
            except AttributeError:
                name = ""

            # Skip tool calls without a valid name
            if not name:
                logger.warning(f"Skipping function call without name: {fc}")
                continue

            calls.append(
                ToolCall(
                    id=name,
                    function=ToolFunctionCall(
                        name=name,
                        arguments=args,
                    ),
                )
            )

        # Return None for text if empty and there are tool calls
        final_text = text if text else None
        return final_text, (calls or None)

    def supports_tools(self) -> bool:
        return True
