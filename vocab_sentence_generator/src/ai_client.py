from __future__ import annotations

import json
import os
import re
from collections.abc import Iterable
from typing import Any

from .models import GenerationResult, Sentence, VocabWord, WordGroup
from .prompt_builder import normalize_difficulty


class AIClient:
    """Replaceable AI client with automatic mock fallback."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        force_mock: bool = False,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self.force_mock = force_mock
        self._client: Any | None = None
        self._init_error: str | None = None

        if self.force_mock or not self.api_key:
            return

        try:
            from openai import OpenAI

            self._client = OpenAI(api_key=self.api_key)
        except Exception as exc:  # pragma: no cover - depends on optional package
            self._init_error = f"OpenAI client 初始化失败：{exc}"

    @property
    def is_mock_mode(self) -> bool:
        return self.force_mock or not self.api_key or self._client is None

    @property
    def mode_name(self) -> str:
        if self.is_mock_mode:
            return "mock"
        return f"openai:{self.model}"

    def generate_for_group(self, group: WordGroup, difficulty: str) -> GenerationResult:
        if self.is_mock_mode:
            error = self._init_error
            return self.mock_result(group, difficulty, error=error)

        try:
            response_text = self._call_openai(group.prompt)
            return self._parse_response(group, response_text)
        except Exception as exc:
            return self.mock_result(group, difficulty, error=f"AI 调用失败，已使用 mock：{exc}")

    def _call_openai(self, prompt: str) -> str:
        if self._client is None:
            raise RuntimeError("OpenAI client is not initialized.")

        try:
            response = self._client.responses.create(
                model=self.model,
                input=prompt,
                temperature=0.3,
            )
            output_text = getattr(response, "output_text", "")
            if output_text:
                return str(output_text)
        except AttributeError:
            pass

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Return only valid JSON for vocabulary learning content.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content or ""

    def _parse_response(self, group: WordGroup, response_text: str) -> GenerationResult:
        payload = _loads_json_object(response_text)

        word_meanings: dict[str, str] = {}
        for item in _as_list(payload.get("word_meanings")):
            if not isinstance(item, dict):
                continue
            word = str(item.get("word", "")).strip()
            meaning = str(
                item.get("chinese_meaning") or item.get("meaning") or ""
            ).strip()
            if word and meaning:
                word_meanings[word] = meaning
                word_meanings[word.lower()] = meaning

        sentences: list[Sentence] = []
        for item in _as_list(payload.get("sentences")):
            if not isinstance(item, dict):
                continue
            english = str(item.get("english", "")).strip()
            chinese = str(item.get("chinese", "")).strip()
            if english:
                sentences.append(Sentence(english=english, chinese=chinese))

        if not sentences:
            fallback = self.mock_result(group, "medium", error="AI 返回内容缺少 sentences。")
            fallback.word_meanings.update(word_meanings)
            return fallback

        for word in group.words:
            if word.word not in word_meanings and word.word.lower() not in word_meanings:
                word_meanings[word.word] = word.chinese_meaning or ""

        return GenerationResult(
            group_id=group.group_id,
            words=group.words,
            word_meanings=word_meanings,
            sentences=sentences,
        )

    def mock_result(
        self,
        group: WordGroup,
        difficulty: str,
        error: str | None = None,
    ) -> GenerationResult:
        normalized_difficulty = normalize_difficulty(difficulty)
        sentences: list[Sentence] = []

        for chunk in _chunks(group.words, 6):
            bold_words = ", ".join(f"**{word.word}**" for word in chunk)
            plain_words = "、".join(word.word for word in chunk)
            sentences.append(
                Sentence(
                    english=(
                        f"This {normalized_difficulty} practice sentence uses "
                        f"{bold_words} together for vocabulary review."
                    ),
                    chinese=(
                        f"这是一句 {normalized_difficulty} 难度的占位例句，"
                        f"包含这些目标词：{plain_words}。"
                    ),
                )
            )

        word_meanings = {
            word.word: word.chinese_meaning or f"{word.word} 的中文含义（mock）"
            for word in group.words
        }
        word_meanings.update({key.lower(): value for key, value in word_meanings.items()})

        return GenerationResult(
            group_id=group.group_id,
            words=group.words,
            word_meanings=word_meanings,
            sentences=sentences,
            error=error,
        )


def _loads_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    if not cleaned.startswith("{"):
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end >= start:
            cleaned = cleaned[start : end + 1]

    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("AI 返回 JSON 不是对象。")
    return payload


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _chunks(items: Iterable[VocabWord], size: int) -> Iterable[list[VocabWord]]:
    chunk: list[VocabWord] = []
    for item in items:
        chunk.append(item)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk
