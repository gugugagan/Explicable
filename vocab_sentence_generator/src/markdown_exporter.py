from __future__ import annotations

from pathlib import Path

from .models import GenerationResult


def _table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def export_markdown(results: list[GenerationResult], output_file: str | Path) -> Path:
    """Write the generated vocabulary plan to a Markdown file."""
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = ["# Vocabulary Sentence Plan", ""]

    for result in results:
        lines.extend([f"## Day {result.group_id}", "", "### Words", ""])
        lines.extend(["| Word | POS | Chinese Meaning |", "|---|---|---|"])

        for word in result.words:
            meaning = (
                result.word_meanings.get(word.word)
                or result.word_meanings.get(word.word.lower())
                or word.chinese_meaning
                or ""
            )
            lines.append(
                f"| {_table_cell(word.word)} | {_table_cell(word.pos)} | {_table_cell(meaning)} |"
            )

        lines.extend(["", "### Sentences", ""])

        if result.error:
            lines.extend([f"> AI generation warning: {_table_cell(result.error)}", ""])

        if not result.sentences:
            lines.append("_No sentences generated._")
        else:
            for index, sentence in enumerate(result.sentences, start=1):
                lines.extend(
                    [
                        f"{index}. {sentence.english}",
                        "",
                        f"中文翻译：{sentence.chinese}",
                        "",
                    ]
                )

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path
