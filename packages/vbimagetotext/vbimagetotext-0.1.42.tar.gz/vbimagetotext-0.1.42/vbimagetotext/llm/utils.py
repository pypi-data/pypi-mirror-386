import base64
import os
from typing import Tuple, Dict


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def make_data_url(image_path: str) -> str:
    _, ext = os.path.splitext(image_path)
    mime = f"image/{ext[1:].lower()}" if ext else "image/png"
    if mime not in ["image/png", "image/jpeg", "image/gif", "image/webp"]:
        mime = "image/png"
    b64 = encode_image(image_path)
    return f"data:{mime};base64,{b64}"


# Simple per-million-token pricing (USD). Override via env if needed.
PRICING_USD: Dict[str, Dict[str, float]] = {
    # Model pricing per 1M tokens (USD), based on provided table (no env overrides)
    # Keys: model -> {"input": x, "cached_input": y, "output": z}
    "gpt-5": {"input": 1.25, "cached_input": 0.125, "output": 10.00},
    "gpt-5-mini": {"input": 0.25, "cached_input": 0.025, "output": 2.00},
    "gpt-5-nano": {"input": 0.05, "cached_input": 0.005, "output": 0.40},
    "gpt-5-chat-latest": {"input": 1.25, "cached_input": 0.125, "output": 10.00},
    "gpt-4.1": {"input": 2.00, "cached_input": 0.50, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.40, "cached_input": 0.10, "output": 1.60},
    "gpt-4.1-nano": {"input": 0.10, "cached_input": 0.025, "output": 0.40},
    "gpt-4o": {"input": 2.50, "cached_input": 1.25, "output": 10.00},
    "gpt-4o-2024-05-13": {"input": 5.00, "cached_input": 5.00, "output": 15.00},
    "gpt-4o-mini": {"input": 0.15, "cached_input": 0.075, "output": 0.60},
    "gpt-realtime": {"input": 4.00, "cached_input": 0.40, "output": 16.00},
    "gpt-4o-realtime-preview": {"input": 5.00, "cached_input": 2.50, "output": 20.00},
    "gpt-4o-mini-realtime-preview": {"input": 0.60, "cached_input": 0.30, "output": 2.40},
    "gpt-audio": {"input": 2.50, "cached_input": 2.50, "output": 10.00},
    "gpt-4o-audio-preview": {"input": 2.50, "cached_input": 2.50, "output": 10.00},
    "gpt-4o-mini-audio-preview": {"input": 0.15, "cached_input": 0.15, "output": 0.60},
    "o1": {"input": 15.00, "cached_input": 7.50, "output": 60.00},
    "o1-pro": {"input": 150.00, "cached_input": 150.00, "output": 600.00},
    "o3-pro": {"input": 20.00, "cached_input": 20.00, "output": 80.00},
    "o3": {"input": 2.00, "cached_input": 0.50, "output": 8.00},
    "o3-deep-research": {"input": 10.00, "cached_input": 2.50, "output": 40.00},
    "o4-mini": {"input": 1.10, "cached_input": 0.275, "output": 4.40},
    "o4-mini-deep-research": {"input": 2.00, "cached_input": 0.50, "output": 8.00},
    "o3-mini": {"input": 1.10, "cached_input": 0.55, "output": 4.40},
    "o1-mini": {"input": 1.10, "cached_input": 0.55, "output": 4.40},
    "codex-mini-latest": {"input": 1.50, "cached_input": 0.375, "output": 6.00},
    "gpt-4o-mini-search-preview": {"input": 0.15, "cached_input": 0.15, "output": 0.60},
    "gpt-4o-search-preview": {"input": 2.50, "cached_input": 2.50, "output": 10.00},
}


def _pricing_for(model: str) -> Dict[str, float]:
    return PRICING_USD.get(model, PRICING_USD.get("o4-mini", {"input": 1.10, "cached_input": 0.275, "output": 4.40}))


def estimate_cost_usd_from_usage(model: str, usage: Dict[str, int]) -> Tuple[float, float, float]:
    p = _pricing_for(model)
    input_tokens = int(usage.get("input_tokens", 0) or 0)
    cached_tokens = int(usage.get("cached_input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    normal_tokens = max(0, input_tokens - cached_tokens)
    usd_in = (normal_tokens / 1_000_000) * \
        p["input"] + (cached_tokens / 1_000_000) * p["cached_input"]
    usd_out = (output_tokens / 1_000_000) * p["output"]
    return usd_in, usd_out, usd_in + usd_out


def estimate_cost_inr_from_usage(model: str, usage: Dict[str, int], exchange_rate: float = 84.0) -> Tuple[float, float, float]:
    usd_in, usd_out, usd_total = estimate_cost_usd_from_usage(model, usage)
    return usd_in * exchange_rate, usd_out * exchange_rate, usd_total * exchange_rate


# Back-compat simple API without cached-token handling
def estimate_cost_inr(model: str, input_tokens: int, output_tokens: int, exchange_rate: float = 88.0) -> Tuple[float, float, float]:
    usage = {"input_tokens": input_tokens,
             "output_tokens": output_tokens, "cached_input_tokens": 0}
    return estimate_cost_inr_from_usage(model, usage, exchange_rate=exchange_rate)
