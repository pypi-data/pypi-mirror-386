"""Minimal example: evaluate against 3 behaviors from the dataset."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from collinear.client import Client


def main() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=True)

    os.environ.setdefault("COLLINEAR_BACKEND_URL", "http://localhost:8000")

    target_model = os.getenv("OPENAI_ASSISTANT_MODEL", "gpt-4o-mini")
    target_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    client = Client(
        assistant_model_url=target_url,
        assistant_model_api_key=os.getenv("OPENAI_API_KEY", ""),
        assistant_model_name=target_model,
        collinear_api_key=os.getenv("COLLINEAR_API_KEY", "demo-placeholder"),
    )

    # Evaluate against 3 behaviors from the server dataset
    print(f"Starting evaluation against 3 behaviors from dataset...")
    start_time = time.time()

    handle = client.redteam(max_prompts=3)
    print(f"Evaluation ID: {handle.id}")

    result = handle.poll(interval=5.0)

    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)

    print(f"Evaluation completed in {minutes}m {seconds}s")

    out = Path(f"redteam_three_intents_{handle.id}.json")
    out.write_text(json.dumps(result, indent=2))
    print(f"Saved results to {out}")


if __name__ == "__main__":
    main()
