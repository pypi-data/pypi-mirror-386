import functools
import logging
import re
from typing import (
    Any,
    Dict,
    Optional,
)

# --- Logging Setup ---
# Use module-level logger, and set DEBUG level for development
logger = logging.getLogger(__name__)

PRICING_URL = "https://github.com/AgentOps-AI/tokencost/blob/main/pricing_table.md"


def _approx_token_count(text: str) -> int:
    # Fallback heuristic for token counting (not used if tiktoken is available)
    if not text:
        return 0
    # Simple heuristic: ~4 characters per token
    return max(0, (len(text) + 3) // 4)


def _count_openai_tokens(text: str, model_name: str) -> int:
    # Try to use tiktoken for token counting if available
    try:
        import tiktoken

        try:
            enc = tiktoken.encoding_for_model(model_name)
        except Exception:
            # Fallbacks: prefer o200k_base (4.1/4o), else cl100k_base
            try:
                enc = tiktoken.get_encoding("o200k_base")
            except Exception:
                enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return _approx_token_count(text)


def _usage_dict(prompt_tokens: Optional[int], completion_tokens: Optional[int]) -> Dict[str, int]:  # NEW
    return {
        "prompt_tokens": int(prompt_tokens or 0),
        "completion_tokens": int(completion_tokens or 0),
    }


def _extract_openai_usage(resp: Any, input_text: str, output_text: str, model_name: str) -> Dict[str, int]:  # NEW
    prompt_tokens = None
    completion_tokens = None
    try:
        usage = getattr(resp, "usage", None)
        if usage is None and isinstance(resp, dict):
            usage = resp.get("usage")

        def _get(obj, key):
            if obj is None:
                return None
            if isinstance(obj, dict):
                return obj.get(key)
            return getattr(obj, key, None)

        prompt_tokens = _get(usage, "input_tokens") or _get(usage, "prompt_tokens")
        completion_tokens = _get(usage, "output_tokens") or _get(usage, "completion_tokens")
    except Exception:
        pass
    if prompt_tokens is None:
        prompt_tokens = _count_openai_tokens(input_text, model_name)
    if completion_tokens is None:
        completion_tokens = _count_openai_tokens(output_text, model_name)
    return _usage_dict(prompt_tokens, completion_tokens)


def _extract_gemini_usage(resp: Any, input_text: str, output_text: str) -> Dict[str, int]:  # NEW
    prompt_tokens = None
    completion_tokens = None
    try:
        um = getattr(resp, "usage_metadata", None)
        if um is None and isinstance(resp, dict):
            um = resp.get("usage_metadata")

        def _get(obj, key):
            if obj is None:
                return None
            if isinstance(obj, dict):
                return obj.get(key)
            return getattr(obj, key, None)

        prompt_tokens = _get(um, "prompt_token_count")
        completion_tokens = _get(um, "candidates_token_count")
    except Exception:
        pass
    if prompt_tokens is None:
        prompt_tokens = _approx_token_count(input_text)
    if completion_tokens is None:
        completion_tokens = _approx_token_count(output_text)
    return _usage_dict(prompt_tokens, completion_tokens)


# Estimate costs using pricing_table.md (best-effort parser)
@functools.lru_cache(maxsize=8)
def _parse_pricing(path: str) -> Dict[str, Dict[str, Optional[float]]]:
    # Explicit type for mypy
    rates: Dict[str, Dict[str, Optional[float]]] = {}
    try:

        def _read_text(src: str) -> str:
            if re.match(r"^https?://", src, re.I):
                # Normalize GitHub "blob" URL to raw content
                m = re.match(
                    r"^https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.*)$",
                    src,
                    re.I,
                )
                if m:
                    src = f"https://raw.githubusercontent.com/{m.group(1)}/{m.group(2)}/{m.group(3)}/{m.group(4)}"
                import urllib.request

                req = urllib.request.Request(src, headers={"User-Agent": "pyopl/1.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return resp.read().decode("utf-8", errors="replace")
            # Fallback to local file if not a URL
            return open(src, "r", encoding="utf8").read()

        txt = _read_text(path)
    except Exception as exc:
        # make failure visible rather than silently returning empty rates
        import logging

        logging.getLogger(__name__).warning("Failed to load pricing from %s: %s", path, exc)
        return rates

    # helpers to parse amounts and units, normalizing to "per 1M"
    def _cell_to_per_1m(cell: str, default_unit: Optional[str] = None) -> Optional[float]:
        if not cell:
            return None
        # find numeric value (allow commas)
        m = re.search(r"\$?([\d,]*\.?\d+)", cell)
        if not m:
            return None
        val = float(m.group(1).replace(",", ""))
        # detect explicit unit in the same cell
        if re.search(r"/\s*1\s*[kK]\b|per\s+1\s*[kK]\b", cell):
            return val * 1000.0
        if re.search(r"/\s*1\s*[mM]\b|per\s+1\s*[mM]\b", cell):
            return val
        # fallback to default unit from header if provided
        if default_unit == "1k":
            return val * 1000.0
        return val

    # Explicit type so assigning "1k"/"1m" is valid
    header_units: Dict[str, Optional[str]] = {"prompt": None, "completion": None}

    for line in txt.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("|"):
            cols = [c.strip() for c in s.strip("|").split("|")]
            if len(cols) >= 3:
                # Skip markdown alignment/separator rows like |:---|:---|...|
                if all(re.fullmatch(r":?-{3,}:?", c) for c in cols[:3]):
                    continue

                c0 = cols[0].lower()
                c1 = cols[1].lower()
                c2 = cols[2].lower()
                if "model" in c0 and (("prompt" in c1 or "completion" in c1) or ("prompt" in c2 or "completion" in c2)):
                    # capture units from header if present
                    if re.search(r"1\s*[kK]", cols[1]):
                        header_units["prompt"] = "1k"
                    elif re.search(r"1\s*[mM]", cols[1]):
                        header_units["prompt"] = "1m"
                    else:
                        header_units["prompt"] = None
                    if re.search(r"1\s*[kK]", cols[2]):
                        header_units["completion"] = "1k"
                    elif re.search(r"1\s*[mM]", cols[2]):
                        header_units["completion"] = "1m"
                    else:
                        header_units["completion"] = None
                    continue

                def _num_with_header(x, which):
                    return _cell_to_per_1m(x, default_unit=header_units.get(which))

                model = cols[0].strip().lower()
                p_val = _num_with_header(cols[1], "prompt")
                c_val = _num_with_header(cols[2], "completion")
                # Only store rows with at least one numeric price
                if p_val is not None or c_val is not None:
                    rates[model] = {
                        "prompt_per_1M": p_val,
                        "completion_per_1M": c_val,
                    }
                continue
        # inline style: "model: prompt $X / 1K, completion $Y / 1K"
        m = re.match(r"(?P<model>[\w\-\._/:@]+)\s*[:\-]\s*(?P<rest>.*)", s, re.I)
        if m:
            model = m.group("model").lower()
            rest = m.group("rest")
            p_match = re.search(r"prompt[^$]*\$?([\d,]*\.?\d+[^,]*)", rest, re.I)
            c_match = re.search(r"completion[^$]*\$?([\d,]*\.?\d+[^,]*)", rest, re.I)
            p_val = _cell_to_per_1m(p_match.group(1)) if p_match else None
            c_val = _cell_to_per_1m(c_match.group(1)) if c_match else None
            if p_val is not None or c_val is not None:
                rates[model] = {"prompt_per_1M": p_val, "completion_per_1M": c_val}
    return rates


def clear_pricing_cache():
    """Clear cached pricing so the URL will be fetched again."""
    _parse_pricing.cache_clear()


def estimate_costs(args, usage):
    pricing = _parse_pricing(PRICING_URL)
    model_key = args.model.lower()
    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")

    def _find_model_entry(key):
        if key in pricing:
            return pricing[key]
        # try substring matches
        for k, v in pricing.items():
            if key in k or k in key:
                return v
        return None

    est = {}
    entry = _find_model_entry(model_key)
    logger.debug(f"Estimating costs for model '{args.model}' using pricing entry: {entry}")
    if entry and prompt_tokens is not None:
        p_rate = entry.get("prompt_per_1M")
        if p_rate is not None:
            est["prompt_cost"] = p_rate * (prompt_tokens / 1000000.0)
        c_rate = entry.get("completion_per_1M")
        if c_rate is not None and completion_tokens is not None:
            est["completion_cost"] = c_rate * (completion_tokens / 1000000.0)
    est["total_cost"] = est.get("prompt_cost", 0.0) + est.get("completion_cost", 0.0)
    return est


def exercise_estimate_costs(model=None):
    """
    Exercise estimate_costs using the snapshot:
    {'prompt_tokens': 21549, 'completion_tokens': 7091}
    """
    usage = {"prompt_tokens": 21549, "completion_tokens": 7091}
    model = model or "gpt-4.1"

    # Choose a model: use given, else first from pricing_table.md, else a common default
    if model is None:
        pricing = _parse_pricing(PRICING_URL)
        model = next(iter(pricing.keys()), None) or "gpt-4o"

    from types import SimpleNamespace

    args = SimpleNamespace(model=model)

    est = estimate_costs(args, usage)
    print({"model": model, "usage": usage, "estimated_costs": est})
    return est


if __name__ == "__main__":
    exercise_estimate_costs()
