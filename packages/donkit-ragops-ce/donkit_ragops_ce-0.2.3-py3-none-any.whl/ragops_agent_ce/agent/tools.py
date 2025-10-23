from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any, Callable

from ..db import kv_get, migrate, open_db
from ..llm import ToolFunction, ToolSpec


class AgentTool:
    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: Callable[[dict[str, Any]], str],
    ) -> None:
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler

    def to_tool_spec(self) -> ToolSpec:
        return ToolSpec(
            function=ToolFunction(
                name=self.name, description=self.description, parameters=self.parameters
            )
        )


# Built-in tools


def tool_time_now() -> AgentTool:
    def _handler(_: dict[str, Any]) -> str:
        now = _dt.datetime.now().isoformat()
        return now

    return AgentTool(
        name="time_now",
        description="Return current local datetime in ISO format",
        parameters={"type": "object", "properties": {}, "additionalProperties": False},
        handler=_handler,
    )


def tool_db_get() -> AgentTool:
    def _handler(args: dict[str, Any]) -> str:
        key = str(args.get("key", ""))
        if not key:
            return ""
        with open_db() as db:
            migrate(db)
            val = kv_get(db, key)
            return "" if val is None else val

    return AgentTool(
        name="db_get",
        description="Get a value from local key-value store by key",
        parameters={
            "type": "object",
            "properties": {"key": {"type": "string"}},
            "required": ["key"],
            "additionalProperties": False,
        },
        handler=_handler,
    )


def tool_list_directory() -> AgentTool:
    def _handler(args: dict[str, Any]) -> str:
        path_str = str(args.get("path", "."))
        try:
            path = Path(path_str).expanduser().resolve()
            if not path.exists():
                return json.dumps({"error": f"Path does not exist: {path_str}"})
            if not path.is_dir():
                return json.dumps({"error": f"Path is not a directory: {path_str}"})

            items = []
            for item in sorted(path.iterdir()):
                try:
                    is_dir = item.is_dir()
                    size = None if is_dir else item.stat().st_size
                    items.append(
                        {
                            "name": item.name,
                            "path": str(item),
                            "is_directory": is_dir,
                            "size_bytes": size,
                        }
                    )
                except (PermissionError, OSError):
                    # Skip items we can't access
                    continue

            return json.dumps(
                {
                    "path": str(path),
                    "items": items,
                    "total_items": len(items),
                }
            )
        except Exception as e:
            return json.dumps({"error": str(e)})

    return AgentTool(
        name="list_directory",
        description=(
            "List contents of a directory with file/folder info. "
            "Returns JSON with items array containing name, path, is_directory, "
            "and size_bytes for each item."
        ),
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the directory to list (supports ~ for home directory)",
                }
            },
            "required": ["path"],
            "additionalProperties": False,
        },
        handler=_handler,
    )
