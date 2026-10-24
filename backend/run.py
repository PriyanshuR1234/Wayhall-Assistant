"""
FastAPI Server Launcher
Run with: .venv/bin/python run.py
"""

import uvicorn

if __name__ == "__main__":
    print("\n🚀 Starting Wayhall Municipal Knowledge Assistant Backend on http://localhost:8000")
    print("📖 Interactive OpenAPI documentation: http://localhost:8000/docs")
    print("🩺 Health endpoint: http://localhost:8000/health\n")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
