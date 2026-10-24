# 🔌 Wayhall Civic AI — Anthropic Model Context Protocol (MCP) Server

Expose the **Wayhall Municipal RAG Engine** as native tools for **Claude Desktop**, **Claude Code**, **Cursor**, **Telegram**, and **WhatsApp**.

---

## 🛠️ Exposed MCP Tools

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `ask_municipal_assistant` | `question: str` | Runs full coverage-first RAG pipeline for any resident/caseworker question. Returns grounded answer, verified citations (PDF name, page number, section), and document gap notices. |
| `search_bylaw_clauses` | `query: str`, `doc_filter: Optional[str]`, `limit: int = 5` | Hybrid search directly inside raw PDF chunks. Returns exact passages, 1-indexed page numbers, and section names. Filter by `'bylaws'`, `'permits'`, or `'service_requests'`. |
| `get_municipal_corpus_summary` | *(none)* | Returns catalog overview of all 3 indexed Cedarhaven municipal documents (pages, chunks, coverage topics). |

---

## 🌐 1. Connecting to Claude.ai Web App (Remote MCP / SSE)

You can connect directly to Claude on the web ([claude.ai](https://claude.ai)) using the live SSE tunnel:

### Credentials to Enter in Claude.ai:
- **Server Name**: `Wayhall-Assistant` (or `wayhall-municipal`)
- **Server URL**: `https://registrar-receipt-cloudy-becomes.trycloudflare.com/sse` *(or `/mcp`)*

### How to Add:
1. Open [claude.ai](https://claude.ai) and go to **Settings** → **Connectors** (or **Developer Settings** / **Add MCP Server**).
2. Enter the **Name** and paste the **Server URL** above.
3. Save and start a new chat. You will see the civic assistant tools active!

> 💡 **Tip:** To restart or re-generate the tunnel anytime, simply run:
> ```bash
> ./backend/mcp_server/tunnel.sh
> ```

---

## 💻 2. Connecting to Claude Desktop

### macOS
1. Open or create the Claude Desktop configuration file:
   ```bash
   code ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```
2. Add the `wayhall-municipal` server under `mcpServers`:
   ```json
   {
     "mcpServers": {
       "wayhall-municipal": {
         "command": "/Users/priyanshurajput/projects/RagChatbot/backend/.venv/bin/python",
         "args": ["-m", "mcp_server.server"],
         "cwd": "/Users/priyanshurajput/projects/RagChatbot/backend",
         "env": {
           "PYTHONPATH": "/Users/priyanshurajput/projects/RagChatbot/backend"
         }
       }
     }
   }
   ```
3. Restart **Claude Desktop**. You will see the hammer icon 🔨 with `ask_municipal_assistant`, `search_bylaw_clauses`, and `get_municipal_corpus_summary` enabled!

### Windows
Edit `%APPDATA%\Claude\claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "wayhall-municipal": {
      "command": "C:\\path\\to\\RagChatbot\\backend\\.venv\\Scripts\\python.exe",
      "args": ["-m", "mcp_server.server"],
      "cwd": "C:\\path\\to\\RagChatbot\\backend"
    }
  }
}
```

---

## ⚡ 2. Connecting to Claude Code (CLI)

Add the MCP server directly to Claude Code with one command:

```bash
claude mcp add wayhall-assistant -- /Users/priyanshurajput/projects/RagChatbot/backend/.venv/bin/python -m mcp_server.server
```

Now, inside your terminal Claude Code session, you can ask:
> *"Query the municipal assistant tool to find out when building permits are required for decks in Cedarhaven."*

Claude Code will automatically call `ask_municipal_assistant` and format the response.

---

## 🤖 3. Connecting to Telegram Bot

Because the RAG engine is modular, you can connect a Telegram bot in under 30 lines of code:

### Install Telegram Bot Library
```bash
pip install python-telegram-bot
```

### Run Telegram Bot Script (`telegram_bot.py`)
```python
import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from app.core.rag.pipeline import run_rag_pipeline

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏛️ Welcome to Wayhall Municipal Assistant! Ask me any question about Cedarhaven bylaws, permits, or service requests."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text
    await update.message.chat.send_action("typing")
    
    result = await run_rag_pipeline(user_question=user_query, history=[])
    
    response = result.answer
    if result.citations:
        response += "\n\n📚 **Verified Citations:**"
        for cit in result.citations[:3]:
            response += f"\n• {cit.source} (Page {cit.page}) § {cit.section or ''}"
            
    await update.message.reply_text(response, parse_mode="Markdown")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Telegram bot running...")
    app.run_polling()
```

---

## 📱 4. Connecting to WhatsApp (via Twilio Webhook)

To connect WhatsApp, configure a Twilio webhook pointing to your FastAPI backend:

```python
from fastapi import APIRouter, Form, Response
from twilio.twiml.messaging_response import MessagingResponse
from app.core.rag.pipeline import run_rag_pipeline

router = APIRouter()

@router.post("/api/whatsapp")
async def whatsapp_webhook(Body: str = Form(...)):
    result = await run_rag_pipeline(user_question=Body, history=[])
    
    resp = MessagingResponse()
    msg = resp.message()
    msg.body(f"{result.answer}\n\n(Source: Cedarhaven Municipal Library)")
    return Response(content=str(resp), media_type="application/xml")
```

---

## 🧪 Testing the MCP Server Manually

You can test that the MCP server tools execute properly by running:

```bash
PYTHONPATH=backend backend/.venv/bin/python -c "
import asyncio
from mcp_server.server import ask_municipal_assistant, get_municipal_corpus_summary

async def main():
    print(get_municipal_corpus_summary())
    res = await ask_municipal_assistant('What are the quiet hours for residential noise?')
    print(res)

asyncio.run(main())
"
```
