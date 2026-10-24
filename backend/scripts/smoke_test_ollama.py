"""
P.R.I.M.E. Local Ollama Smoke Test Script.

Validates the end-to-end integration with a real local Ollama instance:
1. Health check & connectivity probe
2. Model inventory & hardware constraint check (<= 8B parameters)
3. Non-streaming chat completion & timing
4. Streaming chat completion & token throughput (tokens/sec)
5. Graceful failure verification if Ollama is not running

Usage:
    python backend/scripts/smoke_test_ollama.py
    python backend/scripts/smoke_test_ollama.py --model llama3.2:3b
    python backend/scripts/smoke_test_ollama.py --base-url http://127.0.0.1:11434
"""

import argparse
import asyncio
import sys
import time

# Ensure backend root is in python path
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.core.ollama_client import OllamaClient  # noqa: E402
from app.core.ollama_errors import (  # noqa: E402
    OllamaHardwareLimitError,
    OllamaModelNotFoundError,
)
from app.schemas.ollama import ChatMessage, ChatRequest  # noqa: E402


async def run_smoke_test(base_url: str, model_tag: str | None) -> int:
    """Execute smoke test against local Ollama service."""
    print("=" * 65)
    print("  P.R.I.M.E. Local AI Runtime — Ollama Smoke Test")
    print(f"  Target: {base_url}")
    print("=" * 65)

    client = OllamaClient(base_url=base_url)

    # ── Step 1: Health & Connectivity Probe ──────────────────────
    print("\n[1/4] Checking Ollama daemon connectivity...")
    health = await client.check_health()

    if not health.is_connected:
        print("\n[RESULT: OFFLINE / UNAVAILABLE]")
        print(f"  Status:       {health.status}")
        print(f"  Error:        {health.error}")
        print("\n  >> Graceful failure verified.")
        print("  >> To run this test against a live instance, start Ollama:")
        print("     1. Open a terminal and run: ollama serve")
        print(f"     2. Pull a small quantized model: ollama pull {client.default_model}")
        print("     3. Re-run this script.")
        await client.close()
        return 0

    print("  -> Connected successfully!")
    print(f"  -> Available models: {health.available_models}")

    if not health.available_models:
        print("\n[WARNING] Ollama is running but no models are downloaded.")
        print(f"  Run 'ollama pull {client.default_model}' to install a small model.")
        await client.close()
        return 0

    # Determine target model
    selected_model = model_tag or (
        client.default_model
        if any(client.default_model in m for m in health.available_models)
        else health.available_models[0]
    )
    print(f"  -> Selected test model: '{selected_model}'")

    # ── Step 2: Hardware Constraint Verification ─────────────────
    print("\n[2/4] Verifying hardware safety constraint (4GB VRAM ceiling)...")
    try:
        client.validate_model_safety(selected_model)
        await client.validate_model_metadata(selected_model)
        print("  -> Model passed hardware safety check (within 4GB VRAM envelope).")
    except OllamaHardwareLimitError as exc:
        print(f"  [ERROR] Model rejected by hardware guardrail: {exc.message}")
        print(f"  Details: {exc.detail}")
        await client.close()
        return 1

    # ── Step 3: Non-Streaming Chat Completion ────────────────────
    print(f"\n[3/4] Testing non-streaming chat with '{selected_model}'...")
    prompt = "Respond with exactly: 'P.R.I.M.E. local inference operational.'"
    request = ChatRequest(
        messages=[ChatMessage(role="user", content=prompt)],
        model=selected_model,
        temperature=0.1,
        stream=False,
    )

    t0 = time.perf_counter()
    try:
        response = await client.chat(request, timeout=45.0)
        elapsed = time.perf_counter() - t0
        print(f"  -> Reply: {response.message.content.strip()}")
        print(f"  -> Eval tokens: {response.eval_count}")
        print(f"  -> Duration: {elapsed:.2f}s (reported: {response.total_duration_ms}ms)")
        if response.eval_count and elapsed > 0:
            speed = response.eval_count / elapsed
            print(f"  -> Generation speed: {speed:.1f} tokens/second")
    except OllamaModelNotFoundError as exc:
        print(f"  [ERROR] Model not found: {exc.detail}")
        await client.close()
        return 1
    except Exception as exc:
        print(f"  [ERROR] Non-streaming chat failed: {exc}")
        await client.close()
        return 1

    # ── Step 4: Streaming Chat Completion ────────────────────────
    print(f"\n[4/4] Testing streaming chat tokens with '{selected_model}'...")
    stream_request = ChatRequest(
        messages=[ChatMessage(role="user", content="Count from 1 to 5.")],
        model=selected_model,
        temperature=0.1,
        stream=True,
    )

    stream_tokens = 0
    t0_stream = time.perf_counter()
    sys.stdout.write("  -> Stream: ")
    sys.stdout.flush()

    try:
        async for chunk in client.chat_stream(stream_request, timeout=45.0):
            sys.stdout.write(chunk.message.content)
            sys.stdout.flush()
            if chunk.eval_count:
                stream_tokens = chunk.eval_count
        stream_elapsed = time.perf_counter() - t0_stream
        print()
        print(f"  -> Stream finished in {stream_elapsed:.2f}s ({stream_tokens} tokens)")
    except Exception as exc:
        print(f"\n  [ERROR] Streaming chat failed: {exc}")
        await client.close()
        return 1

    await client.close()
    print("\n" + "=" * 65)
    print("  ALL REAL-MODEL SMOKE TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="P.R.I.M.E. Ollama Smoke Test")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:11434",
        help="Ollama daemon URL",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Specific model to test (defaults to configured model or first available)",
    )
    args = parser.parse_args()

    exit_code = asyncio.run(run_smoke_test(args.base_url, args.model))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
