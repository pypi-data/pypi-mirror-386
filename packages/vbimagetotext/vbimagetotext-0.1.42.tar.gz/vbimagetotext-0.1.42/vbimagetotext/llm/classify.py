import json
from typing import Dict, List, Tuple
from openai import OpenAI

from .utils import make_data_url
from ..agentic.curriculum import CURRICULUM, format_for_prompt


def _extract_output_text(resp) -> str:
    # Prefer the convenience property if available
    txt = getattr(resp, "output_text", None)
    if isinstance(txt, str) and txt.strip():
        return txt
    # Fallback: iterate over output structure
    try:
        parts: List = resp.output  # type: ignore[attr-defined]
        out_chunks: List[str] = []
        for p in parts:
            for c in getattr(p, "content", []) or []:
                t = getattr(c, "text", None)
                if isinstance(t, str):
                    out_chunks.append(t)
        return "\n".join(out_chunks)
    except Exception:
        return ""


def _chapter_list() -> List[str]:
    return list(CURRICULUM.keys())


def _all_topics() -> List[str]:
    out: List[str] = []
    for ts in CURRICULUM.values():
        out.extend(ts)
    # de-duplicate while preserving order
    seen = set()
    uniq = []
    for t in out:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def classify_image(image_path: str, model: str, allowed_types: List[str]) -> Tuple[Dict[str, object], Dict[str, int]]:
    client = OpenAI()
    data_url = make_data_url(image_path)

    # Create the classification prompt with curriculum mapping
    chapters_list = ", ".join(_chapter_list())
    topics_list = ", ".join(_all_topics())
    mapping_text = format_for_prompt()

    resp = client.responses.create(
        model=model,
        input=[
            {
                "role": "developer",
                "content": [
                    {"type": "input_text", "text": "You are a precise classifier for exam-problem images. Return ONLY strict JSON."},
                    {"type": "input_text", "text": "Valid chapters and topics are below. Topics must come from the chosen chapter."},
                    {"type": "input_text", "text": mapping_text},
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            f"Classify this physics problem image. Respond ONLY valid JSON with keys: "
                            f"type, subject, chapter, topics, difficulty, contains_diagram. "
                            f"type must be one of {allowed_types}. "
                            f"subject should be 'Physics'. "
                            f"chapter must be one of: {chapters_list}. "
                            f"topics should be an array of 1-3 topics that belong to the chosen chapter. "
                            f"If unsure, pick the closest match from the chapter's list. "
                            f"difficulty should be 'Easy', 'Medium', or 'Hard'. "
                            f"contains_diagram should be true/false. "
                            f"No extra text."
                        ),
                    },
                    {
                        "type": "input_image",
                        "image_url": data_url,
                    },
                ],
            },
        ],
        text={"format": {"type": "text"}},
        reasoning={"effort": "medium"},
        tools=[],
        store=True,
    )

    raw = _extract_output_text(resp)
    try:
        data = json.loads(raw)
    except Exception:
        data = {}

    # Handle topics as either array or single string
    topics = data.get("topics", [])
    if isinstance(topics, str):
        topics = [topics.strip()]
    elif isinstance(topics, list):
        topics = [str(t).strip() for t in topics if str(t).strip()]

    out = {
        "type": str(data.get("type", "")).strip(),
        "subject": str(data.get("subject", "Physics")).strip(),
        "chapter": str(data.get("chapter", "")).strip(),
        "topics": topics,
        # Backward compatibility
        "topic": topics[0] if topics else str(data.get("topic", "")).strip(),
        "difficulty": str(data.get("difficulty", "Medium")).strip(),
        "contains_diagram": bool(data.get("contains_diagram", False)),
    }
    t = out["type"].lower()
    if t not in [x.lower() for x in allowed_types]:
        out["type"] = "mcq_sc"
    usage = {
        "input_tokens": getattr(getattr(resp, "usage", None), "input_tokens", 0) or 0,
        "output_tokens": getattr(getattr(resp, "usage", None), "output_tokens", 0) or 0,
        "total_tokens": getattr(getattr(resp, "usage", None), "total_tokens", 0) or 0,
    }
    return out, usage
