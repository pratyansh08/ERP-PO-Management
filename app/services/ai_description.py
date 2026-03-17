from __future__ import annotations

from typing import Optional

import httpx

from app.core.config import settings


def fallback_description(product_name: str) -> str:
    return (
        f"This is a high-quality {product_name} designed for efficiency and durability. "
        "Ideal for modern business needs."
    )


async def generate_product_description(product_name: str) -> str:
    """
    Returns a professional 2-line description.
    Uses OpenAI if OPENAI_API_KEY is configured; otherwise uses fallback.
    """
    if not settings.openai_api_key:
        return fallback_description(product_name)

    prompt = (
        "Write a professional product description in exactly 2 lines. "
        "Keep it concise and business-appropriate.\n\n"
        f"Product: {product_name}"
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": settings.openai_model,
                    "messages": [
                        {"role": "system", "content": "You write concise B2B product copy."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.6,
                    "max_tokens": 120,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text: Optional[str] = (
                data.get("choices", [{}])[0].get("message", {}).get("content")
                if isinstance(data, dict)
                else None
            )
            if not text:
                return fallback_description(product_name)

            # Normalize to 2 lines if model returned extra whitespace.
            lines = [ln.strip() for ln in str(text).splitlines() if ln.strip()]
            if len(lines) >= 2:
                return "\n".join(lines[:2])
            return lines[0] if lines else fallback_description(product_name)
    except Exception:
        return fallback_description(product_name)

