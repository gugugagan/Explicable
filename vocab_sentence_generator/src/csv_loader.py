from __future__ import annotations

import csv
from pathlib import Path

from .models import VocabWord


WORD_COLUMNS = {
    "word",
    "words",
    "vocabulary",
    "vocab",
    "term",
    "english",
    "englishword",
    "englishwords",
    "英文",
    "英文单词",
    "单词",
}

POS_COLUMNS = {
    "pos",
    "partofspeech",
    "part_of_speech",
    "speech",
    "wordtype",
    "type",
    "词性",
}

MEANING_COLUMNS = {
    "meaning",
    "chinesemeaning",
    "chinese_meaning",
    "definition",
    "translation",
    "中文",
    "中文释义",
    "释义",
    "含义",
}

CSV_ENCODINGS = ("utf-8-sig", "utf-8", "gb18030")


def _normalize_header(value: str) -> str:
    return (
        value.strip()
        .lower()
        .replace("\ufeff", "")
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
        .replace("/", "")
    )


def _find_column(fieldnames: list[str], candidates: set[str]) -> str | None:
    normalized_candidates = {_normalize_header(item) for item in candidates}
    for field in fieldnames:
        if _normalize_header(field) in normalized_candidates:
            return field
    return None


def load_words_from_csv(file_path: str | Path) -> list[VocabWord]:
    """Load vocabulary rows from a CSV file with tolerant column matching."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV 文件不存在：{path}")
    if not path.is_file():
        raise ValueError(f"CSV 路径不是文件：{path}")

    last_decode_error: UnicodeDecodeError | None = None
    for encoding in CSV_ENCODINGS:
        try:
            return _read_csv_with_encoding(path, encoding)
        except UnicodeDecodeError as exc:
            last_decode_error = exc
            continue

    if last_decode_error:
        raise ValueError(f"无法识别 CSV 文件编码：{last_decode_error}") from last_decode_error
    raise ValueError("CSV 文件读取失败。")


def _read_csv_with_encoding(path: Path, encoding: str) -> list[VocabWord]:
    try:
        with path.open("r", encoding=encoding, newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            fieldnames = reader.fieldnames or []
            if not fieldnames:
                raise ValueError("CSV 文件缺少表头。")

            word_col = _find_column(fieldnames, WORD_COLUMNS)
            pos_col = _find_column(fieldnames, POS_COLUMNS)
            meaning_col = _find_column(fieldnames, MEANING_COLUMNS)

            if not word_col or not pos_col:
                available = ", ".join(fieldnames)
                raise ValueError(
                    "CSV 必须包含 word 和 pos 字段，或常见同义字段。"
                    f" 当前字段：{available}"
                )

            words: list[VocabWord] = []
            for row_number, row in enumerate(reader, start=2):
                raw_word = (row.get(word_col) or "").strip()
                if not raw_word:
                    continue

                raw_pos = (row.get(pos_col) or "").strip() or "unknown"
                raw_meaning = ""
                if meaning_col:
                    raw_meaning = (row.get(meaning_col) or "").strip()

                words.append(
                    VocabWord(word=raw_word, pos=raw_pos, chinese_meaning=raw_meaning)
                )

            if not words:
                raise ValueError("CSV 中没有解析到有效单词。")
            return words
    except csv.Error as exc:
        raise ValueError(f"CSV 格式错误：{exc}") from exc


def preview_words(words: list[VocabWord], limit: int = 20) -> list[VocabWord]:
    return words[:limit]
