# Municipal PDF Documents Directory

Place the three Wayhall technical assignment PDF files into this directory:

1. **Service Request Management PDF** (e.g., `service_requests.pdf` or `Service Request Management.pdf`)
2. **Municipal By-laws PDF** (e.g., `bylaws.pdf` or `Municipal By-laws.pdf`)
3. **Permits & Licensing PDF** (e.g., `permits.pdf` or `Permits & Licensing.pdf`)

### Run Ingestion
Once the PDFs are placed in this folder, run:
```bash
.venv/bin/python -m app.ingestion.ingest data/
```
The ingestion script will:
- Extract text page-by-page preserving original 1-indexed page numbers.
- Auto-detect sections and chapter headers.
- Split into semantically balanced chunks with deterministic IDs.
- Generate dense vector embeddings using Google Gemini (`gemini-embedding-001`, 768 dimensions).
- Upsert chunks into your live Supabase database with vector indexes and Full-Text Search (tsvector).
