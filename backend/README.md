# ⚙️ Wayhall Civic AI — FastAPI RAG Backend

FastAPI backend powering the **Wayhall Municipal Knowledge Assistant**. Features parallel multi-document retrieval (dense vector + full-text search), Reciprocal Rank Fusion (RRF) reranking, conversational follow-up contextualization, and strict grounding verification.

---

## 🛠️ Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com) + [Uvicorn](https://www.uvicorn.org)
- **Database**: [Supabase](https://supabase.com) (PostgreSQL + `pgvector` + `tsvector`)
- **LLM**: Google Gemini 3.5 Flash Lite (`models/gemini-3.5-flash-lite`) via `google-generativeai`
- **Embeddings**: Google Gemini Embedding (`models/gemini-embedding-001`, 768 dimensions)
- **PDF Extraction**: [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/)
- **Configuration**: [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- **Model Context Protocol**: [mcp](https://modelcontextprotocol.io) (Anthropic MCP standard)

---

## 🚀 Setup & Execution

### 1. Initialize Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your Supabase project URL, secret key, and Google Gemini API key.

### 3. Database Migration
Run the SQL script [`schema.sql`](file:///Users/priyanshurajput/projects/RagChatbot/backend/schema.sql) in your Supabase SQL Editor to provision the tables, vector indexes, and RPC search functions.

### 4. Ingest Municipal Documents
```bash
python -m app.ingestion.ingest data/
```

### 5. Launch Backend Server
```bash
python run.py
```

The server will be accessible at:
- **API Base**: `http://localhost:8000`
- **Interactive OpenAPI Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

---

## 🔌 Model Context Protocol (MCP) Add-on

The backend includes a standalone Anthropic MCP Server located in [`mcp_server/`](file:///Users/priyanshurajput/projects/RagChatbot/backend/mcp_server).

### Run MCP Server (stdio)
```bash
python -m mcp_server.server
```

### Connect to Claude Desktop
See [`mcp_server/README.md`](file:///Users/priyanshurajput/projects/RagChatbot/backend/mcp_server/README.md) for full configuration details and Telegram/WhatsApp bot examples.
