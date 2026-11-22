import unicodedata


def normalize_answer(text: str) -> str:
    composed = unicodedata.normalize("NFC", text)
    return " ".join(composed.split()).lower()


def is_correct(answer: str, expected: str) -> bool:
    return normalize_answer(answer) == normalize_answer(expected)
