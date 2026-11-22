import random
from collections import Counter

from app.cards.models import Card
from app.reviews.answers import normalize_answer
from app.reviews.models import Exercise
from app.study.exercises import build_exercises, pick_options


def make_card(
    card_id: int, word: str, translation: str, description: str | None = None
) -> Card:
    return Card(id=card_id, word=word, translation=translation, description=description)


POOL = [make_card(i, f"word {i}", f"translation {i}") for i in range(1, 21)]


def test_every_card_gets_one_exercise_of_each_kind() -> None:
    exercises = build_exercises(POOL[:10], POOL, random.Random(42))

    counts = Counter((exercise.card_id, exercise.exercise) for exercise in exercises)
    assert len(exercises) == 30
    assert set(counts.values()) == {1}
    assert {kind for _, kind in counts} == set(Exercise)


def test_choice_exercises_have_six_unique_options_including_the_answer() -> None:
    exercises = build_exercises(POOL[:10], POOL, random.Random(42))

    for exercise in exercises:
        if exercise.exercise == Exercise.TYPE_WORD:
            assert exercise.options == []
            continue
        assert len(exercise.options) == 6
        assert exercise.answer in exercise.options
        assert len({normalize_answer(option) for option in exercise.options}) == 6


def test_prompts_match_the_kind_of_exercise() -> None:
    card = make_card(1, "der Hund", "the dog", "a pet")

    exercises = {
        e.exercise: e for e in build_exercises([card], POOL, random.Random(42))
    }

    assert (
        exercises[Exercise.CHOOSE_WORD].prompt,
        exercises[Exercise.CHOOSE_WORD].answer,
    ) == (
        "the dog",
        "der Hund",
    )
    assert exercises[Exercise.CHOOSE_WORD].description == "a pet"
    assert exercises[Exercise.CHOOSE_TRANSLATION].prompt == "der Hund"
    assert exercises[Exercise.CHOOSE_TRANSLATION].answer == "the dog"
    assert exercises[Exercise.CHOOSE_TRANSLATION].description is None
    assert exercises[Exercise.TYPE_WORD].prompt == "the dog"
    assert exercises[Exercise.TYPE_WORD].answer == "der Hund"


def test_small_course_gives_fewer_options() -> None:
    options = pick_options("word 1", ["word 1", "word 2", "word 3"], random.Random(42))

    assert sorted(options) == ["word 1", "word 2", "word 3"]


def test_options_never_repeat_the_answer_or_each_other() -> None:
    pool = ["der Hund", "Der  Hund", "die Katze", "die  katze", "das Haus"]

    options = pick_options("der Hund", pool, random.Random(42))

    assert sorted(normalize_answer(option) for option in options) == [
        "das haus",
        "der hund",
        "die katze",
    ]


def test_exercises_are_shuffled_across_cards() -> None:
    exercises = build_exercises(POOL[:10], POOL, random.Random(1))

    card_order = [exercise.card_id for exercise in exercises]
    assert card_order != sorted(card_order)
