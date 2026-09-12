# ---------------------------------------------------------------------------
# AI service — wraps calls to the Gemini API
# ---------------------------------------------------------------------------
# Why a service module?
#   • Keeps LLM details (URL, payload shape, error handling) out of routes.
#   • Reusable: call `summarize_text(...)` from any endpoint or background
#     task. If we later add "auto-summarize on publish", we call the same
#     function.
#   • Testable: you can unit-test `summarize_text` in isolation, mocking
#     the HTTP layer, without spinning up FastAPI.
# ---------------------------------------------------------------------------

import httpx
# httpx → modern async HTTP client. Same API as `requests`, but
#         supports `await`. We use it for the outbound call to Gemini.

from ..config import settings
# settings.GEMINI_API_KEY — read from .env at import time.


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-2.5-flash:generateContent"
)
# The endpoint format is:
#   {BASE}/{MODEL}:generateContent?key=API_KEY
# We build the full URL at call time so we can append the API key as a
# query param without hard-coding secrets in source.

TIMEOUT_SECONDS = 30.0
# LLM calls can be slow. 30 s is generous but bounded — anything longer
# and something is likely wrong (bad key, network, model outage).


# ---------------------------------------------------------------------------
# CUSTOM EXCEPTION
# ---------------------------------------------------------------------------

class SummarizationError(Exception):
    """Raised when the AI service fails for any reason.

    Why a custom exception? Routes shouldn't need to know whether the
    failure was a network glitch, a bad API key, or a malformed response.
    They just catch SummarizationError and return a clean 502.
    """
    pass


# ---------------------------------------------------------------------------
# PROMPT BUILDER
# ---------------------------------------------------------------------------

def _build_prompt(text: str) -> str:
    """Wrap the user's content in a clear instruction for the LLM.

    Being explicit about length/format keeps output predictable — no
    "Sure, here's a summary:" preamble, no markdown unless asked.
    """
    return (
        "Summarize the following blog post in 2 to 3 sentences. "
        "Be concise, factual, and neutral. "
        "Do not start with phrases like 'This article' or 'The post'. "
        "Return only the summary text, no headings, no markdown.\n\n"
        "---\n"
        f"{text}\n"
        "---"
    )


# ---------------------------------------------------------------------------
# MAIN FUNCTION
# ---------------------------------------------------------------------------

async def summarize_text(text: str) -> str:
    """
    Send `text` to Gemini and return the generated summary.

    Raises SummarizationError on any failure so callers have one
    exception type to worry about.
    """
    # (a) Fail fast if the key is missing. This is a config error, not a
    #     transient failure — a clear message here saves a lot of debugging.
    if not settings.GEMINI_API_KEY:
        raise SummarizationError(
            "GEMINI_API_KEY is not set. Add it to your .env file."
        )

    # (b) Guard against silly inputs. The route already validates the post
    #     exists and has content, but it's cheap to double-check here too.
    if not text or not text.strip():
        raise SummarizationError("Cannot summarize empty text.")

    # (c) Build the request payload. Gemini's API shape is:
    #     { "contents": [ { "parts": [ { "text": "..." } ] } ] }
    #     If you later switch to Groq/OpenAI, only this dict changes.
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": _build_prompt(text)}
                ]
            }
        ],
        # generationConfig tunes the model. temperature=0.3 keeps the
        # output factual and consistent — higher values → more creativity.
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 256,
        },
    }

    # (d) The API key goes in the URL as a query param.
    params = {"key": settings.GEMINI_API_KEY}

    # (e) Async HTTP call inside a context manager so the connection is
    #     closed as soon as we're done. `async with` is the async analog
    #     of `with`.
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.post(GEMINI_URL, params=params, json=payload)
        # httpx doesn't raise on 4xx/5xx by default — we must call
        # raise_for_status() to convert a bad status into an exception.
        response.raise_for_status()
    except httpx.TimeoutException as exc:
        # Network-level failure: the LLM took too long.
        raise SummarizationError(f"Gemini request timed out: {exc}") from exc
    except httpx.HTTPStatusError as exc:
        # We got a response, but it was 4xx/5xx. Include the response body
        # (truncated) — it usually contains the real reason (bad key,
        # quota exceeded, etc.).
        body = exc.response.text[:300]
        raise SummarizationError(
            f"Gemini returned {exc.response.status_code}: {body}"
        ) from exc
    except httpx.RequestError as exc:
        # DNS failure, connection refused, TLS error, etc.
        raise SummarizationError(f"Network error calling Gemini: {exc}") from exc

    # (f) Parse the response. Gemini wraps the text deep inside:
    #     { "candidates": [ { "content": { "parts": [ { "text": "..." } ] } } ] }
    #     We walk the structure defensively — any missing key becomes a
    #     clean SummarizationError instead of a KeyError traceback.
    try:
        data = response.json()
        summary = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError, ValueError) as exc:
        raise SummarizationError(
            f"Unexpected Gemini response shape: {response.text[:300]}"
        ) from exc

    # (g) Some models can return an empty string (rare, but possible when
    #     safety filters kick in). Treat that as a failure too.
    if not summary:
        raise SummarizationError("Gemini returned an empty summary.")

    return summary