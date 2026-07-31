"""Minimal direct LLM smoke test for the official baseline project."""

from __future__ import annotations

import argparse

from llm_client import InternChatClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ask Intern-S one question directly.")
    parser.add_argument("question", nargs="*", help="Question text")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max_tokens", type=int, default=4096)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    question = " ".join(args.question).strip()
    if not question:
        question = input("请输入问题：").strip()

    client = InternChatClient()
    response = client.chat(
        messages=[{"role": "user", "content": question}],
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )
    print(response)


if __name__ == "__main__":
    main()
