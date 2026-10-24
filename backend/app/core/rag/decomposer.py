"""
Conversational Query Decomposer & Contextualizer.
Rewrites ambiguous follow-up questions using conversation history into standalone,
search-optimized sub-queries for municipal document retrieval.
"""

import asyncio
import json
import re
from typing import List, Optional, Tuple

import google.generativeai as genai

from app.config import settings
from app.utils.logger import get_logger
from app.utils.retry import retry_sync

logger = get_logger(__name__)
genai.configure(api_key=settings.GEMINI_API_KEY)

DECOMP_WITH_HISTORY_PROMPT = """You are a conversational query analyzer for a municipal knowledge retrieval system for Cedarhaven.
Given the recent conversation history and the user's latest message:
1. If the latest message is a follow-up, clarification, re-phrasing, simplification request, or partial query (e.g. "explain more properly", "timing", "what about weekends?", "who do I call?", "what are the fees?", "tell me more"):
   - Rewrite it into a complete, standalone question that preserves the exact topic from the conversation history.
   - Extract 1–4 specific, search-optimized keywords/phrases (sub_queries) to retrieve the relevant municipal documents.
2. If the latest message is a completely new topic or independent question:
   - Formulate a clear standalone question and 1–4 search phrases.

Output ONLY valid JSON:
{{
  "standalone_question": "<self-contained question>",
  "sub_queries": ["phrase1", "phrase2"]
}}
Do NOT include explanations outside the JSON.

Conversation History:
{history_text}

Latest User Message: {question}"""

DECOMP_PROMPT = """You are a query analyzer for a municipal knowledge retrieval system for Cedarhaven.
Given a user's question, identify the distinct retrieval topics it covers.
Return 1–4 short search phrases (not full sentences) optimized for document search.

Output ONLY valid JSON:
{{
  "standalone_question": "{question}",
  "sub_queries": ["phrase1", "phrase2"]
}}
Do NOT include explanations outside the JSON.

User question: {question}"""


def _format_history_text(history: List[dict]) -> str:
    turns = []
    for msg in history[-6:]:  # last 3 turns
        role = "User" if msg.get("role") == "user" else "Assistant"
        content = (msg.get("content") or "").strip()
        # Trim very long assistant answers to avoid context bloat
        if len(content) > 300:
            content = content[:300] + "..."
        turns.append(f"{role}: {content}")
    return "\n".join(turns)


@retry_sync(attempts=2, base_delay=1.0)
def _decompose_sync(question: str, history: Optional[List[dict]] = None) -> Tuple[str, List[str]]:
    model = genai.GenerativeModel(settings.GEMINI_LLM_MODEL)

    if history and len(history) > 0:
        history_text = _format_history_text(history)
        prompt = DECOMP_WITH_HISTORY_PROMPT.format(history_text=history_text, question=question)
    else:
        prompt = DECOMP_PROMPT.format(question=question)

    resp = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.0,
            max_output_tokens=1000,
        ),
    )
    raw = (resp.text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

    try:
        parsed = json.loads(raw)
    except Exception:
        return question, [question]

    standalone = question
    queries = [question]

    if isinstance(parsed, dict):
        standalone = parsed.get("standalone_question") or question
        queries = parsed.get("sub_queries") or [question]
    elif isinstance(parsed, list):
        queries = parsed

    # Deduplicate, strip whitespace, filter empty
    seen = set()
    result = []
    for q in queries:
        if isinstance(q, str):
            q_clean = q.strip()
            if q_clean and q_clean.lower() not in seen:
                seen.add(q_clean.lower())
                result.append(q_clean)

    # Ensure standalone is also clean
    if not standalone or not isinstance(standalone, str):
        standalone = question

    return standalone, (result or [question])


async def decompose_query(
    question: str,
    history: Optional[List[dict]] = None,
) -> Tuple[str, List[str]]:
    """
    Return a tuple of (standalone_question, list_of_sub_queries).
    Takes conversation history into account to resolve pronouns, follow-ups, and partial queries.
    """
    try:
        standalone, sub_queries = await asyncio.to_thread(_decompose_sync, question, history)
        logger.info(
            "Contextualized '%s' → standalone='%s' | sub_queries=%s",
            question[:50],
            standalone[:60],
            sub_queries,
        )
        return standalone, sub_queries
    except Exception as exc:
        logger.warning("Query decomposition failed (%s) — using original query.", exc)
        return question, [question]
