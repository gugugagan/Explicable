from __future__ import annotations

from collections import OrderedDict, deque

from .models import VocabWord, WordGroup


PREFERRED_POS_ORDER = (
    "noun",
    "verb",
    "adjective",
    "adverb",
    "pronoun",
    "preposition",
    "conjunction",
    "interjection",
    "determiner",
    "phrase",
    "unknown",
)

POS_ALIASES = {
    "n": "noun",
    "n.": "noun",
    "noun": "noun",
    "v": "verb",
    "v.": "verb",
    "verb": "verb",
    "vi": "verb",
    "vt": "verb",
    "adj": "adjective",
    "adj.": "adjective",
    "adjective": "adjective",
    "adv": "adverb",
    "adv.": "adverb",
    "adverb": "adverb",
    "prep": "preposition",
    "prep.": "preposition",
    "preposition": "preposition",
    "pron": "pronoun",
    "pron.": "pronoun",
    "pronoun": "pronoun",
    "conj": "conjunction",
    "conj.": "conjunction",
    "conjunction": "conjunction",
    "interj": "interjection",
    "interj.": "interjection",
    "interjection": "interjection",
    "det": "determiner",
    "determiner": "determiner",
    "phrase": "phrase",
}


def canonical_pos(pos: str) -> str:
    normalized = pos.strip().lower()
    compact = normalized.replace(" ", "").replace("_", "").replace("-", "")
    return POS_ALIASES.get(normalized) or POS_ALIASES.get(compact) or normalized or "unknown"


def group_words(words: list[VocabWord], daily_count: int) -> list[WordGroup]:
    """Create stable groups while cycling through different parts of speech."""
    if daily_count <= 0:
        raise ValueError("每日背词数量必须是正整数。")
    if not words:
        return []

    buckets: OrderedDict[str, deque[VocabWord]] = OrderedDict()
    for word in words:
        key = canonical_pos(word.pos)
        buckets.setdefault(key, deque()).append(word)

    ordered_keys = [key for key in PREFERRED_POS_ORDER if key in buckets]
    ordered_keys.extend(key for key in buckets.keys() if key not in PREFERRED_POS_ORDER)

    groups: list[WordGroup] = []
    group_id = 1

    while any(buckets[key] for key in ordered_keys):
        selected: list[VocabWord] = []
        while len(selected) < daily_count and any(buckets[key] for key in ordered_keys):
            progressed = False
            for key in ordered_keys:
                if len(selected) >= daily_count:
                    break
                if buckets[key]:
                    selected.append(buckets[key].popleft())
                    progressed = True
            if not progressed:
                break

        groups.append(WordGroup(group_id=group_id, words=selected))
        group_id += 1

    return groups
