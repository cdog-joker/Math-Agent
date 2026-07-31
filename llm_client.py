"""Local Intern-S API client and demo fallback client.

The official evaluator injects its own client into ``ReasoningAgent``.
This module is only for local development.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Dict, List, Optional

from utils.env_loader import load_dotenv


class InternChatClient:
    """Minimal OpenAI-compatible chat client for local testing."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: int = 120,
        thinking_mode: Optional[bool] = None,
    ):
        self.api_key = api_key or os.getenv("INTERN_API_KEY", "")
        self.model = model or os.getenv("INTERN_MODEL", "intern-s2-preview")
        self.api_base = self._normalize_api_base(
            api_base
            or os.getenv("INTERN_API_BASE", "")
            or "https://chat.intern-ai.org.cn/api/v1"
        )
        self.timeout = timeout
        self.thinking_mode = (
            thinking_mode
            if thinking_mode is not None
            else _parse_optional_bool(os.getenv("INTERN_THINKING_MODE", ""))
        )

        if not self.api_key:
            raise RuntimeError("INTERN_API_KEY is not set")

    def chat(self, messages: List[Dict[str, str]], temperature=0.2, max_tokens=4096):
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if self.thinking_mode is not None:
            payload["thinking_mode"] = self.thinking_mode

        request = urllib.request.Request(
            url=f"{self.api_base}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Intern API HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Intern API request failed: {exc}. "
                f"Please check INTERN_API_BASE={self.api_base}"
            ) from exc

    @staticmethod
    def _normalize_api_base(api_base: str) -> str:
        base = api_base.rstrip("/")
        suffix = "/chat/completions"
        if base.endswith(suffix):
            return base[: -len(suffix)]
        return base


class InternMessagesClient:
    """Claude-like client for https://chat.intern-ai.org.cn/v1/messages."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 120,
    ):
        self.api_key = api_key or os.getenv("INTERN_API_KEY", "")
        self.api_url = (
            api_url
            or os.getenv("INTERN_API_URL", "")
            or os.getenv("INTERN_API_BASE", "")
            or "https://chat.intern-ai.org.cn/v1/messages"
        ).rstrip("/")
        self.model = model or os.getenv("INTERN_MODEL", "intern-s1")
        self.timeout = timeout

        if self.api_url.endswith("/api/v1"):
            self.api_url = self.api_url + "/chat/completions"
        if not self.api_url.endswith("/v1/messages"):
            self.api_url = "https://chat.intern-ai.org.cn/v1/messages"

        if not self.api_key:
            raise RuntimeError("INTERN_API_KEY is not set")

    def chat(self, messages: List[Dict[str, str]], temperature=0.2, max_tokens=4096):
        system_parts = []
        normalized_messages = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "system":
                system_parts.append(content)
            else:
                normalized_messages.append({"role": role, "content": content})

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": normalized_messages,
            "temperature": temperature,
        }
        if system_parts:
            payload["system"] = "\n\n".join(system_parts)

        request = urllib.request.Request(
            url=self.api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Intern Messages API HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Intern Messages API request failed: {exc}. "
                f"Please check INTERN_API_URL={self.api_url}"
            ) from exc


class DemoRuleClient:
    """Tiny offline client so the project can run before API credentials are set."""

    def chat(self, messages: List[Dict[str, str]], temperature=0.2, max_tokens=4096):
        text = "\n".join(message.get("content", "") for message in messages)

        finite_field = re.search(r"F_\{?81\}?|mathbb\{F\}[_*]\{?81\}?", text)
        generator_set = "F_3" in text or "mathbb{F}_3" in text
        if finite_field and generator_set:
            return (
                "解题思路：F_81/F_3 的扩张次数为4。不能生成整个域的元素正好落在"
                "真子域中；F_81 的真子域只有 F_3 与 F_9，其中 F_3 包含于 F_9。"
                "因此生成元个数为 81-9=72。\n"
                "校验：这些元素的最小多项式次数为4，正好生成 F_81。\n"
                "FINAL_ANSWER: 72"
            )

        arithmetic = re.search(r"(\d+)\s*\+\s*(\d+)", text)
        if arithmetic:
            value = int(arithmetic.group(1)) + int(arithmetic.group(2))
            return f"解题思路：直接相加。\n校验：计算无误。\nFINAL_ANSWER: {value}"

        return (
            "解题思路：当前未配置真实模型，本地DemoRuleClient无法可靠求解该题。\n"
            "校验：请设置 INTERN_API_KEY 后使用 InternChatClient。\n"
            "FINAL_ANSWER: 无法确定"
        )


def build_local_client():
    load_dotenv()
    if os.getenv("INTERN_API_KEY"):
        style = os.getenv("INTERN_API_STYLE", "").strip().lower()
        url = os.getenv("INTERN_API_URL", "") or os.getenv("INTERN_API_BASE", "")
        if style in {"claude", "messages"} or url.rstrip("/").endswith("/v1/messages"):
            return InternMessagesClient()
        return InternChatClient()
    return DemoRuleClient()


def _parse_optional_bool(value: str) -> Optional[bool]:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return None
