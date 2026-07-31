"""Local JSONL runner for the competition agent."""

from __future__ import annotations

import argparse
import traceback
from pathlib import Path

from llm_client import build_local_client
from user_agent import ReasoningAgent
from utils.jsonl import read_jsonl, write_json


def parse_args():
    parser = argparse.ArgumentParser(description="Run ReasoningAgent on a JSONL file.")
    parser.add_argument(
        "--input_file",
        default="sample_data/dev.jsonl",
        help="Path to JSONL input. Each line must include idx and problem.",
    )
    parser.add_argument(
        "--output_dir",
        default="sample_outputs",
        help="Directory where per-problem JSON outputs are written.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Recompute outputs even when idx.json already exists and is non-empty.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    client = build_local_client()
    agent = ReasoningAgent(client=client)

    for item in read_jsonl(args.input_file):
        idx = item.get("idx")
        output_path = output_dir / f"{idx}.json"
        if (
            output_path.exists()
            and output_path.stat().st_size > 0
            and not args.overwrite
        ):
            print(f"skip idx={idx}: {output_path}")
            continue

        problem = item.get("problem", "")
        metadata = {
            key: value
            for key, value in item.items()
            if key not in {"problem", "answer"}
        }
        try:
            result = agent.solve(problem=problem, metadata=metadata)
            final_response = str(result.get("final_response", "")).strip()
            if not final_response:
                raise RuntimeError("Agent returned empty final_response")
            output = {
                "idx": idx,
                "status": "success",
                "final_response": final_response,
                "trace": result.get("trace", []),
            }
        except Exception as exc:
            output = {
                "idx": idx,
                "status": "error",
                "final_response": "",
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "traceback": traceback.format_exc(limit=5),
                },
                "trace": [],
            }

        write_json(output_path, output)
        if output["status"] == "success":
            print(f"idx={idx} final_response={output['final_response']}")
        else:
            print(f"idx={idx} error={output['error']['message']}")
        print(f"wrote: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
