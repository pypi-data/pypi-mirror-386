from __future__ import annotations

import json
import os

import httpx
import mcp
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class SearchQueryArgs(BaseModel):
    query: str = Field(description="Search query text")
    k: int = Field(default=10, description="Number of top results to return")
    rag_service_url: str = Field(
        default="http://localhost:8000",
        description="RAG service base URL (e.g., http://localhost:8000)",
    )


server = mcp.server.FastMCP(
    "rag-query",
    log_level=os.getenv("RAGOPS_LOG_LEVEL", "CRITICAL"),  # noqa
)


@server.tool(
    name="search_documents",
    description=(
        "Search for relevant documents in the RAG vector database. "
        "Returns the most relevant document chunks based on the query."
        "Not use full rag-config, only retriever."
    ).strip(),
)
async def search_documents(args: SearchQueryArgs) -> mcp.types.TextContent:
    """Search for documents using RAG service HTTP API."""
    url = f"{args.rag_service_url.rstrip('/')}/api/query/search"

    # Prepare request payload (only query in body)
    payload = {"query": args.query}

    # k parameter goes as query parameter
    params = {"k": args.k}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, params=params)
            response.raise_for_status()

            result = response.json()

            # Format results for better readability
            formatted_results = {
                "query": args.query,
                "total_results": len(result) if isinstance(result, list) else 0,
                "documents": [],
            }

            # Result is a list of documents
            documents = result if isinstance(result, list) else []
            for doc in documents:
                metadata = doc.get("metadata", {})
                formatted_doc = {
                    "content": doc.get("page_content", "").strip(),
                    "metadata": metadata,
                }
                formatted_results["documents"].append(formatted_doc)

            return mcp.types.TextContent(
                type="text", text=json.dumps(formatted_results, ensure_ascii=False, indent=2)
            )

    except httpx.HTTPStatusError as e:
        error_detail = f"HTTP {e.response.status_code}: {e.response.text}"
        return mcp.types.TextContent(
            type="text",
            text=json.dumps(
                {"error": "HTTP request failed", "detail": error_detail, "url": url},
                ensure_ascii=False,
                indent=2,
            ),
        )
    except httpx.RequestError as e:
        return mcp.types.TextContent(
            type="text",
            text=json.dumps(
                {
                    "error": "Request error",
                    "detail": str(e),
                    "url": url,
                    "hint": "Make sure RAG service is running and accessible",
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
    except Exception as e:
        return mcp.types.TextContent(
            type="text",
            text=json.dumps(
                {"error": "Unexpected error", "detail": str(e)}, ensure_ascii=False, indent=2
            ),
        )


@server.tool(
    name="get_rag_prompt",
    description=(
        "Get a formatted RAG prompt with retrieved context for a query. "
        "Returns ready-to-use prompt string with relevant document chunks embedded."
        "Use full rag-config for prompt generation."
    ).strip(),
)
async def get_rag_prompt(args: SearchQueryArgs) -> mcp.types.TextContent:
    """Get formatted RAG prompt using RAG service HTTP API."""
    url = f"{args.rag_service_url.rstrip('/')}/api/query/prompt"

    # Prepare request payload
    payload = {"query": args.query}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

            # Response is plain text prompt
            prompt = response.text

            return mcp.types.TextContent(type="text", text=prompt)

    except httpx.HTTPStatusError as e:
        error_detail = f"HTTP {e.response.status_code}: {e.response.text}"
        return mcp.types.TextContent(
            type="text",
            text=json.dumps(
                {"error": "HTTP request failed", "detail": error_detail, "url": url},
                ensure_ascii=False,
                indent=2,
            ),
        )
    except httpx.RequestError as e:
        return mcp.types.TextContent(
            type="text",
            text=json.dumps(
                {
                    "error": "Request error",
                    "detail": str(e),
                    "url": url,
                    "hint": "Make sure RAG service is running and accessible",
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
    except Exception as e:
        return mcp.types.TextContent(
            type="text",
            text=json.dumps(
                {"error": "Unexpected error", "detail": str(e)}, ensure_ascii=False, indent=2
            ),
        )


def main() -> None:
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
