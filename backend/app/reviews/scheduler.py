from dataclasses import dataclass
from datetime import datetime, timedelta

LADDER: tuple[timedelta, ...] = (
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
LAST_STEP = len(LADDER) - 1


@dataclass(frozen=True)
class Schedule:
    step: int
    recovery_target: int | None
    due_at: datetime


def start_learning(now: datetime) -> Schedule:
    return Schedule(step=0, recovery_target=None, due_at=now + LADDER[0])


def next_schedule(
    step: int, recovery_target: int | None, *, correct: bool, now: datetime
) -> Schedule:
    if not 0 <= step <= LAST_STEP:
        raise ValueError(f"step must be between 0 and {LAST_STEP}, got {step}")

    if not correct:
        failed_at = max(step, recovery_target or 0)
        return Schedule(
            step=0, recovery_target=failed_at or None, due_at=now + LADDER[0]
        )

    if recovery_target is not None:
        new_step = min(step + 2, recovery_target)
        target = None if new_step >= recovery_target else recovery_target
    else:
        new_step = min(step + 1, LAST_STEP)
        target = None

    return Schedule(
        step=new_step, recovery_target=target, due_at=now + LADDER[new_step]
    )
