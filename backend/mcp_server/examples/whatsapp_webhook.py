"""
Wayhall Civic AI — WhatsApp Webhook Example (Twilio).

Receives incoming WhatsApp messages from residents via Twilio Webhook,
queries the Wayhall Municipal RAG Engine, and responds with grounded answers
and source citations in real-time.

Prerequisites:
    pip install twilio fastapi uvicorn

Usage:
    uvicorn mcp_server.examples.whatsapp_webhook:app --reload --port 8001
"""

import os
import sys
from pathlib import Path

# Ensure backend root is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

from fastapi import FastAPI, Form, Response
try:
    from twilio.twiml.messaging_response import MessagingResponse
except ImportError:
    MessagingResponse = None

from app.core.rag.pipeline import run_rag_pipeline

app = FastAPI(title="Wayhall WhatsApp Webhook")


@app.post("/api/whatsapp")
async def whatsapp_webhook(Body: str = Form(...), From: str = Form(None)):
    """
    Twilio WhatsApp Webhook endpoint.
    Body: User message text
    From: Sender WhatsApp ID (e.g., 'whatsapp:+14155238886')
    """
    user_query = Body.strip()
    
    # Run the coverage-first RAG pipeline
    result = await run_rag_pipeline(user_question=user_query, history=[])
    
    answer_text = result.answer.strip()
    
    # Add brief source citations
    if result.citations:
        citations_summary = ", ".join([f"Page {c.page}" for c in result.citations[:2]])
        answer_text += f"\n\n[Cedarhaven Municipal Records: {citations_summary}]"
        
    if MessagingResponse:
        resp = MessagingResponse()
        msg = resp.message()
        msg.body(answer_text)
        return Response(content=str(resp), media_type="application/xml")
    else:
        # Fallback raw response if twilio library is not installed
        return {"response": answer_text}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mcp_server.examples.whatsapp_webhook:app", host="0.0.0.0", port=8001, reload=True)
