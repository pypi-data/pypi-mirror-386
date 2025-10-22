"""Minimal example: evaluate against all behaviors from the server dataset."""

from __future__ import annotations

import json
import os
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

    print("Starting evaluation against all behaviors from dataset...")
    handle = client.redteam()
    print(f"Evaluation ID: {handle.id}")

    result = handle.poll(interval=5.0)

    out = Path(f"redteam_results_{handle.id}.json")
    out.write_text(json.dumps(result, indent=2))
    print(f"Saved results to {out}")


if __name__ == "__main__":
    main()
