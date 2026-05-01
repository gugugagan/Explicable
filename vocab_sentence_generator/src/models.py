from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class VocabWord:
    word: str
    pos: str
    chinese_meaning: str = ""

    def to_dict(self) -> dict[str, str]:
        data = {"word": self.word, "pos": self.pos}
        if self.chinese_meaning:
            data["chinese_meaning"] = self.chinese_meaning
        return data


@dataclass
class WordGroup:
    group_id: int
    words: list[VocabWord]
    prompt: str = ""


@dataclass(frozen=True)
class Sentence:
    english: str
    chinese: str


@dataclass
class GenerationResult:
    group_id: int
    words: list[VocabWord]
    word_meanings: dict[str, str] = field(default_factory=dict)
    sentences: list[Sentence] = field(default_factory=list)
    error: str | None = None
