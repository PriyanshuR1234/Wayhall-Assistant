"""
Quick smoke test for backend connectivity and dependencies.
"""

import sys

def main():
    print("Testing backend setup...")

    # 1. Config
    try:
        from app.config import settings
        print(" [OK] Configuration loaded")
        print(f"      - Gemini Embed Model: {settings.GEMINI_EMBED_MODEL}")
        print(f"      - Gemini LLM Model:   {settings.GEMINI_LLM_MODEL}")
        print(f"      - Supabase URL:       {settings.SUPABASE_URL[:25]}...")
    except Exception as exc:
        print(f" [FAIL] Configuration load failed: {exc}")
        sys.exit(1)

    # 2. Supabase Connection
    try:
        from app.db.vector_store import count_chunks
        count = count_chunks()
        print(f" [OK] Supabase connected successfully! Chunks currently indexed: {count}")
    except Exception as exc:
        print(f" [FAIL] Supabase connection failed: {exc}")

    # 3. FastAPI App Initialization & Health Endpoint
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        resp = client.get("/health")
        print(f" [OK] Health endpoint status {resp.status_code}: {resp.json()}")
    except Exception as exc:
        print(f" [FAIL] FastAPI test client failed: {exc}")

    print("\nSmoke test complete!")

if __name__ == "__main__":
    main()
