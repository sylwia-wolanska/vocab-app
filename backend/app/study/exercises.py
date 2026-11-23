import random
from collections.abc import Sequence

from app.cards.models import Card
from app.reviews.answers import normalize_answer
from app.reviews.models import Exercise
from app.study.schemas import LearnExercise

OPTION_COUNT = 6


def pick_options(correct: str, pool: Sequence[str], rng: random.Random) -> list[str]:
    seen = {normalize_answer(correct)}
    candidates: list[str] = []
    for value in pool:
        key = normalize_answer(value)
        if key not in seen:
            seen.add(key)
            candidates.append(value)
    distractors = rng.sample(candidates, min(OPTION_COUNT - 1, len(candidates)))
    options = [correct, *distractors]
    rng.shuffle(options)
    return options


def build_exercises(
    cards: Sequence[Card], pool: Sequence[Card], rng: random.Random
) -> list[LearnExercise]:
    words = [card.word for card in pool]
    translations = [card.translation for card in pool]
    exercises: list[LearnExercise] = []

    for card in cards:
        exercises.append(
            LearnExercise(
                card_id=card.id,
                exercise=Exercise.CHOOSE_WORD,
                prompt=card.translation,
                description=card.description,
                options=pick_options(card.word, words, rng),
                answer=card.word,
            )
        )
        exercises.append(
            LearnExercise(
                card_id=card.id,
                exercise=Exercise.CHOOSE_TRANSLATION,
                prompt=card.word,
                description=None,
                options=pick_options(card.translation, translations, rng),
                answer=card.translation,
            )
        )
        exercises.append(
            LearnExercise(
                card_id=card.id,
                exercise=Exercise.TYPE_WORD,
                prompt=card.translation,
                description=card.description,
                options=[],
                answer=card.word,
            )
        )

    rng.shuffle(exercises)
    return exercises
