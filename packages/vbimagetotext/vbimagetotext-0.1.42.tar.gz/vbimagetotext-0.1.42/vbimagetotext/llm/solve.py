from typing import List, Optional, Tuple, Dict
from openai import OpenAI
import os
import json

from .utils import make_data_url


def _extract_output_text(resp) -> str:
    txt = getattr(resp, "output_text", None)
    if isinstance(txt, str) and txt.strip():
        return txt
    try:
        parts = resp.output  # type: ignore[attr-defined]
        out_chunks: List[str] = []
        for p in parts:
            for c in getattr(p, "content", []) or []:
                t = getattr(c, "text", None)
                if isinstance(t, str):
                    out_chunks.append(t)
        return "\n".join(out_chunks)
    except Exception:
        return ""


def solve_with_images(
    prompt_text: str,
    image_paths: List[str],
    model: str = "o4-mini",
    system_prompt: Optional[str] = None,
    reasoning_effort: str = "high",
) -> Tuple[str, Dict[str, int]]:
    client = OpenAI()

    dev_text = (
        system_prompt
        or "You are an expert physicist/mathematician. Use precise LaTeX for answers."
    )

    user_content: List[dict] = [
        {"type": "input_text", "text": prompt_text}
    ]

    # Inject TikZ cache snippets if provided via env var
    tikz_cache_path = os.getenv("VB_TIKZ_CACHE")
    max_cache_chars = int(os.getenv("VB_TIKZ_CACHE_MAX_CHARS", "6000"))
    if tikz_cache_path and os.path.exists(tikz_cache_path):
        try:
            lines = [ln for ln in open(
                tikz_cache_path, "r", encoding="utf-8").read().splitlines() if ln.strip()]
            # Each line JSON with fields: snippet
            snippets: List[str] = []
            total = 0
            for ln in lines:
                try:
                    obj = json.loads(ln)
                    snip = str(obj.get("snippet", "")).strip()
                except Exception:
                    snip = ""
                if not snip:
                    continue
                if total + len(snip) > max_cache_chars:
                    break
                snippets.append(snip)
                total += len(snip)
            if snippets:
                joined = "\n\n".join(snippets)
                user_content.append({
                    "type": "input_text",
                    "text": (
                        "Reference TikZ patterns (reuse idioms when diagramming; do not copy verbatim unless identical):\n"
                        + joined
                    ),
                })
        except Exception:
            pass
    for p in image_paths:
        user_content.append(
            {"type": "input_image", "image_url": make_data_url(p)})

    resp = client.responses.create(
        model=model,
        input=[
            {"role": "developer", "content": [
                {"type": "input_text", "text": dev_text}]},
            {"role": "user", "content": user_content},
        ],
        text={"format": {"type": "text"}},
        reasoning={"effort": reasoning_effort},
        tools=[],
        store=True,
    )
    text = _extract_output_text(resp).strip()
    usage = {
        "input_tokens": getattr(getattr(resp, "usage", None), "input_tokens", 0) or 0,
        "output_tokens": getattr(getattr(resp, "usage", None), "output_tokens", 0) or 0,
        "total_tokens": getattr(getattr(resp, "usage", None), "total_tokens", 0) or 0,
    }
    return text, usage
