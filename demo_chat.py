"""Minimal direct LLM demo.

This script does not use ReasoningAgent, answer extraction, verification, or JSONL.
It only sends one user question to the configured LLM and prints the raw answer.
"""

from __future__ import annotations

import argparse

from llm_client import build_local_client


def parse_args():
    parser = argparse.ArgumentParser(description="Ask the LLM one question directly.")
    parser.add_argument("question", nargs="*", help="Question text")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max_tokens", type=int, default=4096)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    question = " ".join(args.question).strip()
    if not question:
        question = input("请输入问题：").strip()

    client = build_local_client()
    response = client.chat(
        messages=[{"role": "user", "content": question}],
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    print(_extract_text(response))
    return 0


def _extract_text(response) -> str:
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        content = response.get("content")
        if isinstance(content, list):
            texts = [
                item.get("text", "")
                for item in content
                if isinstance(item, dict) and item.get("type") == "text"
            ]
            if texts:
                return "\n".join(texts)
        if isinstance(content, str):
            return content
        choices = response.get("choices")
        if choices and isinstance(choices, list):
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict) and isinstance(message.get("content"), str):
                    return message["content"]
                if isinstance(first.get("text"), str):
                    return first["text"]
        if isinstance(response.get("text"), str):
            return response["text"]
    return str(response)


if __name__ == "__main__":
    raise SystemExit(main())
