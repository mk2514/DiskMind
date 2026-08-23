"""
DiskMind – AI Assistant (LLM Copilot)
Orchestrates tool-calling LLM conversations.
"""
from __future__ import annotations

import json
import os
from typing import Any, AsyncIterator

from openai import AsyncOpenAI

from backend.ai.prompts import SYSTEM_PROMPT
from backend.ai.tools import TOOL_SCHEMAS, TOOL_DISPATCH

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=OPENAI_API_KEY or "demo",
            base_url=OPENAI_BASE_URL,
        )
    return _client


async def chat(
    db,
    messages: list[dict[str, str]],
    stream: bool = False,
) -> dict[str, Any]:
    """
    Run one turn of the AI copilot conversation.
    Handles tool-calling loop internally.
    Returns {"response": str, "tool_calls": list}.
    """
    if not OPENAI_API_KEY:
        return await _demo_response(db, messages)

    client = get_client()
    history = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    tool_calls_made = []
    max_tool_rounds = 5

    for _ in range(max_tool_rounds):
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=history,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            max_tokens=1024,
            temperature=0.3,
        )

        msg = response.choices[0].message

        if not msg.tool_calls:
            return {
                "response": msg.content or "",
                "tool_calls": tool_calls_made,
            }

        # Execute tool calls
        history.append(msg.model_dump(exclude_unset=True))

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments) if tc.function.arguments else {}
            except json.JSONDecodeError:
                args = {}

            if fn_name in TOOL_DISPATCH:
                result = await TOOL_DISPATCH[fn_name](db, args)
            else:
                result = {"error": f"Unknown tool: {fn_name}"}

            tool_calls_made.append({"tool": fn_name, "args": args, "result": result})

            history.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, default=str),
            })

    return {"response": "I've analyzed your storage. Please check the dashboard for details.", "tool_calls": tool_calls_made}


async def _demo_response(db, messages: list[dict]) -> dict[str, Any]:
    """
    Fallback response when no API key is configured.
    Uses tool data to generate a meaningful response without LLM.
    """
    from backend.ai.tools import tool_get_storage_summary, tool_get_recommendations, tool_get_storage_forecast

    summary = await tool_get_storage_summary(db)
    forecast = await tool_get_storage_forecast(db)
    recs = await tool_get_recommendations(db)

    user_msg = messages[-1]["content"].lower() if messages else ""

    thresholds = forecast.get("thresholds", {})
    days_until_90 = thresholds.get("days_until_90pct", 999)
    recoverable_gb = summary.get("total_recoverable_gb", 0)
    dup_gb = summary.get("duplicate_wasted_gb", 0)
    used_gb = summary.get("used_gb", 0)
    total_gb = summary.get("total_gb", 0)
    util = summary.get("utilization_pct", 0)
    daily_growth = forecast.get("avg_daily_growth_bytes", 0) / 1e9

    if "why" in user_msg and ("full" in user_msg or "storage" in user_msg or "disk" in user_msg):
        response = (
            f"Your disk is **{util:.1f}% full** ({used_gb:.1f} GB / {total_gb:.1f} GB). "
            f"I identified **{recoverable_gb:.1f} GB** of potentially recoverable storage, "
            f"primarily from:\n\n"
            f"- 🔴 **Duplicates**: {dup_gb:.1f} GB of identical files\n"
            f"- 🟡 **Caches**: {summary.get('cache_bytes', 0)/1e9:.1f} GB of app cache data\n"
            f"- ⚪ **Inactive files**: {summary.get('inactive_bytes', 0)/1e9:.1f} GB not accessed recently\n\n"
            f"At your current growth rate of **{daily_growth:.2f} GB/day**, your disk will reach "
            f"90% capacity in approximately **{days_until_90} days**."
        )
    elif "safely" in user_msg or "remove" in user_msg or "clean" in user_msg:
        top_recs = recs[:3]
        rec_lines = "\n".join([
            f"- **{r['category'].title()}**: {r['reason']} ({r['size_bytes']/1e9:.1f} GB, {r['risk_level']} risk, {r['confidence']*100:.0f}% confidence)"
            for r in top_recs
        ])
        response = (
            f"Based on my analysis, you can safely recover **{recoverable_gb:.1f} GB** "
            f"with the following LOW-risk actions:\n\n{rec_lines}\n\n"
            f"All actions require your explicit approval before execution. "
            f"Protected system files are never touched."
        )
    elif "when" in user_msg or "forecast" in user_msg or "predict" in user_msg or "90" in user_msg:
        response = (
            f"**Storage Forecast:**\n\n"
            f"- Current utilization: **{util:.1f}%** ({used_gb:.1f} GB / {total_gb:.1f} GB)\n"
            f"- Average daily growth: **{daily_growth:.2f} GB/day**\n"
            f"- **90% capacity**: {days_until_90} days from now\n"
            f"- **95% capacity**: {thresholds.get('days_until_95pct', 999)} days from now\n"
            f"- **100% capacity**: {thresholds.get('days_until_100pct', 999)} days from now\n\n"
            f"If you clean up the recommended {recoverable_gb:.1f} GB, the 90% threshold "
            f"would be delayed by approximately **{int(recoverable_gb / max(daily_growth, 0.01))} days**."
        )
    else:
        response = (
            f"I'm DiskMind, your AI Storage Copilot. Here's your current storage status:\n\n"
            f"- **Health Score**: {summary.get('health_score', 0)}/100\n"
            f"- **Disk Usage**: {util:.1f}% ({used_gb:.1f} GB / {total_gb:.1f} GB)\n"
            f"- **Recoverable**: {recoverable_gb:.1f} GB\n"
            f"- **Days until 90%**: {days_until_90}\n\n"
            f"Try asking: *\"Why is my disk full?\"*, *\"What can I safely remove?\"*, "
            f"or *\"When will I reach 90% capacity?\"*\n\n"
            f"*(Demo mode: Set OPENAI_API_KEY for full AI responses)*"
        )

    return {
        "response": response,
        "tool_calls": [{"tool": "get_storage_summary", "result": summary}],
    }
