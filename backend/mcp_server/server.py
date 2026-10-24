"""
Wayhall Civic AI — Anthropic Model Context Protocol (MCP) Server.

Enables Claude Desktop, Claude Code, Cursor, and agentic workflows to query
Cedarhaven municipal bylaws, service request SLAs, and permits with strict grounding
and zero speculative hallucination.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure the backend directory is in the Python module search path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

from mcp.server.mcpserver import MCPServer
from app.core.rag.pipeline import run_rag_pipeline
from app.core.rag.retriever import retrieve_all_documents
from app.core.rag.reranker import rrf_rerank
from app.utils.logger import get_logger

logger = get_logger("wayhall-mcp")

# Initialize MCP Server
mcp = MCPServer(
    name="Wayhall-Municipal-Assistant",
    description="Official Municipal Knowledge Assistant for Cedarhaven by-laws, permits, and service request SLAs.",
)


@mcp.tool(
    name="ask_municipal_assistant",
    description=(
        "Ask any question about Cedarhaven municipal services, bylaws, or permits. "
        "Returns a strictly grounded answer with verified citations (source PDF, 1-indexed page, section). "
        "Explicitly refuses speculative answers if the topic is not covered in official documents."
    ),
)
async def ask_municipal_assistant(question: str) -> str:
    """
    Run full coverage-first RAG pipeline for a resident or caseworker inquiry.
    """
    try:
        result = await run_rag_pipeline(user_question=question, history=[])
        
        output_lines = [
            f"### Municipal Assistant Answer\n",
            result.answer.strip(),
            "\n",
        ]

        # Add Verified Citations Block
        if result.citations:
            output_lines.append("### Verified Municipal Citations")
            for idx, cit in enumerate(result.citations, start=1):
                section_str = f" — *{cit.section}*" if cit.section else ""
                output_lines.append(
                    f"- **[{idx}] {cit.source}** (Page {cit.page}){section_str}\n"
                    f"  > \"{cit.snippet.strip()}\""
                )
            output_lines.append("")

        # Add Document Gap Notice if any parts are uncovered
        if result.unsupported_parts:
            output_lines.append("### ⚠️ Document Gap Notice")
            output_lines.append(
                "The supplied municipal documents do not contain information on: "
                f"**{', '.join(result.unsupported_parts)}**. "
                "In accordance with municipal guidelines, no speculative answers were invented."
            )
            output_lines.append("")

        return "\n".join(output_lines)
    except Exception as exc:
        logger.error("MCP ask_municipal_assistant error: %s", exc)
        return f"Error executing municipal knowledge retrieval: {str(exc)}"


@mcp.tool(
    name="search_bylaw_clauses",
    description=(
        "Search directly inside Cedarhaven municipal PDF text chunks using hybrid vector + full-text search. "
        "Returns raw excerpts, page numbers, and section headers. "
        "Optional doc_filter: 'bylaws', 'permits', 'service_requests', or leave empty for all."
    ),
)
async def search_bylaw_clauses(
    query: str,
    doc_filter: Optional[str] = None,
    limit: int = 5,
) -> str:
    """
    Direct evidence search across municipal documents.
    """
    try:
        raw_candidates = await retrieve_all_documents([query])
        
        if doc_filter:
            clean_filter = doc_filter.strip().lower()
            raw_candidates = [c for c in raw_candidates if c.doc_label == clean_filter]

        ranked = rrf_rerank(raw_candidates)[:limit]

        if not ranked:
            return f"No municipal clauses found matching query '{query}'."

        lines = [f"Found {len(ranked)} relevant clauses for '{query}':\n"]
        for idx, chunk in enumerate(ranked, start=1):
            sec = f" | Section: {chunk.section}" if chunk.section else ""
            lines.append(
                f"### Passage {idx} [{chunk.chunk_id}]\n"
                f"- **Source**: {chunk.source} (Page {chunk.page}{sec})\n"
                f"- **Text**: {chunk.text.strip()}\n"
            )
        return "\n".join(lines)
    except Exception as exc:
        logger.error("MCP search_bylaw_clauses error: %s", exc)
        return f"Error searching bylaw clauses: {str(exc)}"


@mcp.tool(
    name="get_municipal_corpus_summary",
    description=(
        "Get metadata on the 3 official Cedarhaven municipal PDF documents indexed in the knowledge base, "
        "including page spans, chunk counts, and coverage topics."
    ),
)
def get_municipal_corpus_summary() -> str:
    """
    Return overview of the indexed Cedarhaven municipal documents.
    """
    summary = """
# Cedarhaven Municipal Document Library

1. **01_Cedarhaven_Service_Request_Management.pdf**
   - **Domain**: Service Requests & Public Works (`service_requests`)
   - **Pages**: 1–8 (32 chunks indexed)
   - **Topics**: 311 intake, P1/P2/P3 prioritization, response timelines, potholes, streetlights, waste collection, illegal dumping.

2. **02_Cedarhaven_Bylaw_Enforcement.pdf**
   - **Domain**: Municipal By-laws (`bylaws`)
   - **Pages**: 1–8 (30 chunks indexed)
   - **Topics**: Quiet hours (10:00 PM–7:00 AM), routine construction noise hours, property standards, on-street parking (3-hour continuous limit, winter overnight parking ban), fences, animal controls, enforcement.

3. **03_Cedarhaven_Permits_and_Licensing.pdf**
   - **Domain**: Building Permits & Licences (`permits`)
   - **Pages**: 1–8 (30 chunks indexed)
   - **Topics**: Small detached storage sheds (≤ 12 m², ≤ 3 m height exemption rules), decks (> 0.6 m permit requirement), application reviews, business licensing, sidewalk patios, security deposits.

**Total**: 92 chunks embedded in Supabase pgvector (768d cosine) with tsvector full-text search.
"""
    return summary.strip()


def main():
    """Entry point for running the MCP server over stdio or Streamable HTTP/SSE."""
    import argparse
    import uvicorn
    from mcp.server.transport_security import TransportSecuritySettings
    from starlette.routing import Route

    parser = argparse.ArgumentParser(description="Wayhall Civic AI MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http", "http"],
        default="stdio",
        help="Transport protocol (stdio, sse, streamable-http, or http)",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host address for HTTP/SSE")
    parser.add_argument("--port", type=int, default=8005, help="Port for HTTP/SSE")
    args = parser.parse_args()

    if args.transport in ("sse", "streamable-http", "http"):
        # Disable DNS rebinding checks to allow public tunneling (Cloudflare, ngrok, localhost.run, etc.)
        security = TransportSecuritySettings(enable_dns_rebinding_protection=False)
        
        # Build StreamableHTTP app supporting POST/GET handshakes required by Claude.ai Web
        app = mcp.streamable_http_app(
            streamable_http_path="/sse",
            transport_security=security,
            host=args.host,
        )
        # Register /mcp and root / so any endpoint entered into Claude.ai connects seamlessly
        app.routes.append(Route("/mcp", endpoint=app.routes[0].endpoint))
        app.routes.append(Route("/", endpoint=app.routes[0].endpoint))

        print(
            f"🏛️ Starting Wayhall Municipal MCP Server on http://{args.host}:{args.port} (endpoints: /sse, /mcp, /)...",
            file=sys.stderr,
        )
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    else:
        print("🏛️ Starting Wayhall Municipal MCP Server (STDIO)...", file=sys.stderr)
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()


