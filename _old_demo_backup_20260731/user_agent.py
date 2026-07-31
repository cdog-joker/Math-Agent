"""Competition entry point for the Math-Agent demo.

The evaluator imports ``ReasoningAgent`` from this file and calls:

    agent = ReasoningAgent(client=official_client)
    agent.solve(problem: str, metadata: dict) -> dict

Keep this file free of hard-coded secrets and absolute paths.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from utils.answer_utils import extract_final_answer, normalize_final_answer
from utils.prompt_loader import load_prompt


@dataclass
class Candidate:
    answer: str
    reasoning_summary: str
    raw_response: str


class ReasoningAgent:
    """Math reasoning agent with a fixed competition-compatible interface."""

    def __init__(self, client, *args, **kwargs):
        self.client = client
        self.model_name = kwargs.get("model_name", "")
        self.system_prompt = load_prompt("math_system.txt")
        self.solver_prompt = load_prompt("solver_prompt.txt")
        self.verifier_prompt = load_prompt("verifier_prompt.txt")
        self.solve_temperature = _get_float_env("AGENT_SOLVE_TEMPERATURE", 0.2)
        self.verify_temperature = _get_float_env("AGENT_VERIFY_TEMPERATURE", 0.0)
        self.solve_max_tokens = _get_int_env("AGENT_SOLVE_MAX_TOKENS", 4096)
        self.verify_max_tokens = _get_int_env("AGENT_VERIFY_MAX_TOKENS", 2048)

    def solve(self, problem: str, metadata: dict) -> dict:
        trace: List[Dict[str, str]] = []

        if not isinstance(problem, str) or not problem.strip():
            return {
                "final_response": "无法解析题目",
                "trace": [{"step": "input_check", "content": "problem为空或类型非法"}],
            }

        metadata = metadata or {}
        trace.append(
            {
                "step": "plan",
                "content": "构造数学解题提示词，生成候选答案，再进行答案抽取和格式规整。",
            }
        )

        try:
            primary = self._generate_solution(
                problem,
                metadata,
                temperature=self.solve_temperature,
                max_tokens=self.solve_max_tokens,
            )
            candidates = [primary]
            trace.append(
                {
                    "step": "primary_candidate",
                    "content": self._short_trace(primary.reasoning_summary),
                }
            )

            # A low-cost second pass is useful for formatting and catching obvious slips.
            verified = self._verify_candidate(problem, metadata, primary)
            if verified:
                candidates.append(verified)
                trace.append(
                    {
                        "step": "verification_candidate",
                        "content": self._short_trace(verified.reasoning_summary),
                    }
                )

            selected = self._select_candidate(candidates)
            final_response = normalize_final_answer(selected.answer)
            if not final_response:
                final_response = normalize_final_answer(
                    extract_final_answer(selected.raw_response)
                )

            trace.append(
                {
                    "step": "finalize",
                    "content": f"最终答案规整为：{final_response}",
                }
            )

            return {
                "final_response": final_response or "无法确定",
                "trace": trace,
            }
        except Exception as exc:  # Keep evaluator calls from crashing the runner.
            trace.append({"step": "error", "content": f"{type(exc).__name__}: {exc}"})
            return {
                "final_response": "无法确定",
                "trace": trace,
            }

    def _generate_solution(
        self,
        problem: str,
        metadata: dict,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> Candidate:
        prompt = self.solver_prompt.format(
            problem=problem.strip(),
            metadata=json.dumps(metadata, ensure_ascii=False),
        )
        response = self._chat(prompt, temperature=temperature, max_tokens=max_tokens)
        return Candidate(
            answer=extract_final_answer(response),
            reasoning_summary=response,
            raw_response=response,
        )

    def _verify_candidate(
        self, problem: str, metadata: dict, candidate: Candidate
    ) -> Optional[Candidate]:
        prompt = self.verifier_prompt.format(
            problem=problem.strip(),
            metadata=json.dumps(metadata, ensure_ascii=False),
            candidate_answer=candidate.answer,
            candidate_solution=candidate.raw_response,
        )
        response = self._chat(
            prompt,
            temperature=self.verify_temperature,
            max_tokens=self.verify_max_tokens,
        )
        answer = extract_final_answer(response)
        if not answer:
            return None
        return Candidate(answer=answer, reasoning_summary=response, raw_response=response)

    def _select_candidate(self, candidates: List[Candidate]) -> Candidate:
        normalized_counts: Dict[str, int] = {}
        for candidate in candidates:
            normalized = normalize_final_answer(candidate.answer)
            if normalized:
                normalized_counts[normalized] = normalized_counts.get(normalized, 0) + 1

        if normalized_counts:
            best_answer = max(
                normalized_counts.items(), key=lambda item: (item[1], len(item[0]))
            )[0]
            for candidate in reversed(candidates):
                if normalize_final_answer(candidate.answer) == best_answer:
                    return candidate

        return candidates[0]

    def _chat(self, user_prompt: str, temperature: float, max_tokens: int) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        response = self.client.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return self._extract_client_text(response)

    @staticmethod
    def _extract_client_text(response: Any) -> str:
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
            if isinstance(response.get("text"), str):
                return response["text"]
            choices = response.get("choices")
            if choices and isinstance(choices, list):
                first = choices[0]
                if isinstance(first, dict):
                    message = first.get("message", {})
                    if isinstance(message, dict) and isinstance(
                        message.get("content"), str
                    ):
                        return message["content"]
                    if isinstance(first.get("text"), str):
                        return first["text"]
        return str(response)

    @staticmethod
    def _short_trace(text: str, limit: int = 500) -> str:
        compact = re.sub(r"\s+", " ", text).strip()
        if len(compact) <= limit:
            return compact
        return compact[: limit - 3] + "..."


def _get_int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _get_float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default
