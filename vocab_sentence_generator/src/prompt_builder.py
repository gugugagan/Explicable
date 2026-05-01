from __future__ import annotations

import json

from .models import WordGroup


VALID_DIFFICULTIES = {"easy", "medium", "hard"}


def normalize_difficulty(difficulty: str) -> str:
    normalized = difficulty.strip().lower()
    if normalized not in VALID_DIFFICULTIES:
        return "medium"
    return normalized


def build_prompt(group: WordGroup, difficulty: str = "medium") -> str:
    """Build a stable JSON-output prompt for one vocabulary group."""
    normalized_difficulty = normalize_difficulty(difficulty)
    words_json = json.dumps(
        [word.to_dict() for word in group.words],
        ensure_ascii=False,
        indent=2,
    )

    return f"""You are an English vocabulary sentence generator for Chinese learners.

Difficulty: {normalized_difficulty}

Target words:
{words_json}

Task:
1. Write one or more natural English sentences.
2. Use as many target words as possible, preferably all of them.
3. In English sentences, wrap every target word in Markdown bold, for example **apple**.
4. Provide a Chinese translation for each English sentence.
5. Provide a concise Chinese meaning for every target word.
6. Keep the difficulty aligned with the selected level: easy, medium, or hard.

Output only valid JSON. Do not include Markdown fences or explanations.

Required JSON schema:
{{
  "word_meanings": [
    {{
      "word": "apple",
      "pos": "noun",
      "chinese_meaning": "苹果"
    }}
  ],
  "sentences": [
    {{
      "english": "I **eat** an **apple** every morning.",
      "chinese": "我每天早上吃一个苹果。"
    }}
  ]
}}
"""
