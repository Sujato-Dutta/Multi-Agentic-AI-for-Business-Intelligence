"""Resilient LLM client with cascading model fallback."""

import logging
import re
import time

from groq import Groq
from dotenv import load_dotenv

from config import MODELS, MODEL_FALLBACK_CHAIN

load_dotenv()
logger = logging.getLogger(__name__)

_client = Groq()

# Pattern to strip <think>...</think> reasoning blocks from models like Qwen3/DeepSeek
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def _strip_thinking(text: str) -> str:
    """Remove chain-of-thought <think> blocks and clean up the result."""
    cleaned = _THINK_RE.sub("", text).strip()
    # Also remove stray closing tags or partial tags
    cleaned = cleaned.replace("</think>", "").replace("<think>", "").strip()
    return cleaned


def call_llm(requested_model_key: str, prompt: str) -> str:
    """Call Groq LLM with automatic fallback through MODEL_FALLBACK_CHAIN."""
    starting_model = MODELS.get(requested_model_key, MODELS["fast"])
    try:
        start_idx = MODEL_FALLBACK_CHAIN.index(starting_model)
    except ValueError:
        start_idx = 0

    chain = MODEL_FALLBACK_CHAIN[start_idx:] + MODEL_FALLBACK_CHAIN[:start_idx]

    last_error = None
    for model in chain:
        try:
            logger.info("Calling LLM model: %s", model)
            response = _client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=2048,
            )
            raw = response.choices[0].message.content or ""
            return _strip_thinking(raw)
        except Exception as e:
            last_error = e
            logger.warning("Model %s failed: %s. Shifting to fallback.", model, e)
            time.sleep(1.5)

    raise RuntimeError(f"All models in fallback chain failed. Last error: {last_error}")
