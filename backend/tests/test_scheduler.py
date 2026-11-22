from datetime import UTC, datetime, timedelta

import pytest

from app.reviews.scheduler import LADDER, LAST_STEP, next_schedule, start_learning

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def walk(
    step: int, target: int | None, answers: list[bool]
) -> list[tuple[int, int | None, timedelta]]:
    results = []
    for correct in answers:
        schedule = next_schedule(step, target, correct=correct, now=NOW)
        step, target = schedule.step, schedule.recovery_target
        results.append((step, target, schedule.due_at - NOW))
    return results


def test_ladder_matches_the_specification() -> None:
    assert LADDER == (
        timedelta(hours=4),
        timedelta(hours=8),
        timedelta(days=1),
        timedelta(days=2),
        timedelta(days=4),
        timedelta(weeks=1),
        timedelta(weeks=2),
        timedelta(days=30),
        timedelta(days=60),
        timedelta(days=120),
        timedelta(days=180),
    )


def test_learning_starts_at_step_0_due_in_4_hours() -> None:
    schedule = start_learning(NOW)

    assert (schedule.step, schedule.recovery_target) == (0, None)
    assert schedule.due_at == NOW + timedelta(hours=4)


@pytest.mark.parametrize("step", range(LAST_STEP))
def test_correct_answer_moves_one_step_up(step: int) -> None:
    schedule = next_schedule(step, None, correct=True, now=NOW)

    assert schedule.step == step + 1
    assert schedule.due_at == NOW + LADDER[step + 1]


def test_top_step_stays_at_6_months() -> None:
    assert walk(LAST_STEP, None, [True, True]) == [
        (10, None, timedelta(days=180)),
        (10, None, timedelta(days=180)),
    ]


def test_example_from_the_specification() -> None:
    assert walk(6, None, [False, True, True, True, True]) == [
        (0, 6, timedelta(hours=4)),
        (2, 6, timedelta(days=1)),
        (4, 6, timedelta(days=4)),
        (6, None, timedelta(weeks=2)),
        (7, None, timedelta(days=30)),
    ]


def test_recovery_never_jumps_past_the_target() -> None:
    assert walk(5, None, [False, True, True, True, True]) == [
        (0, 5, timedelta(hours=4)),
        (2, 5, timedelta(days=1)),
        (4, 5, timedelta(days=4)),
        (5, None, timedelta(weeks=1)),
        (6, None, timedelta(weeks=2)),
    ]


def test_wrong_answer_while_recovering_keeps_the_original_target() -> None:
    assert walk(6, None, [False, True, False, True]) == [
        (0, 6, timedelta(hours=4)),
        (2, 6, timedelta(days=1)),
        (0, 6, timedelta(hours=4)),
        (2, 6, timedelta(days=1)),
    ]


def test_wrong_answer_at_step_0_has_nothing_to_recover() -> None:
    assert walk(0, None, [False]) == [(0, None, timedelta(hours=4))]


def test_wrong_answer_at_step_1_recovers_in_one_answer() -> None:
    assert walk(1, None, [False, True, True]) == [
        (0, 1, timedelta(hours=4)),
        (1, None, timedelta(hours=8)),
        (2, None, timedelta(days=1)),
    ]


@pytest.mark.parametrize("step", [-1, LAST_STEP + 1])
def test_impossible_step_raises(step: int) -> None:
    with pytest.raises(ValueError, match="step must be between 0 and 10"):
        next_schedule(step, None, correct=True, now=NOW)
