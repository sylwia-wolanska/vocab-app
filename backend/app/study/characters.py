import unicodedata
from collections.abc import Iterable


def graphemes(text: str) -> list[str]:
    clusters: list[str] = []
    for char in text:
        if clusters and unicodedata.combining(char):
            clusters[-1] += char
        else:
            clusters.append(char)
    return clusters


def special_characters(words: Iterable[str]) -> list[str]:
    found: set[str] = set()
    for word in words:
        text = unicodedata.normalize("NFC", word.lower())
        for cluster in graphemes(text):
            if not cluster.isascii() and not cluster.isspace():
                found.add(cluster)
    return sorted(found)
