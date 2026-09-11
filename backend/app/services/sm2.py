"""SM-2 Spaced Repetition Algorithm.

Quality ratings: Again(0), Hard(2), Good(3), Easy(5)

If quality >= 3: successful recall, increase interval
If quality < 3: failed, reset to 1 day

Ease factor always updated, minimum 1.3
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

RATING_TO_QUALITY = {"again": 0, "hard": 2, "good": 3, "easy": 5}


@dataclass
class ReviewResult:
    repetitions: int
    interval: float
    ease_factor: float
    due_at: datetime


def calculate_sm2(
    quality: int,
    repetitions: int = 0,
    interval: float = 0.0,
    ease_factor: float = 2.5,
    review_time: Optional[datetime] = None,
) -> ReviewResult:
    if review_time is None:
        review_time = datetime.now(timezone.utc)
    quality = max(0, min(5, quality))

    if quality >= 3:
        if repetitions == 0:
            new_interval = 1.0
        elif repetitions == 1:
            new_interval = 6.0
        else:
            new_interval = interval * ease_factor
        new_reps = repetitions + 1
    else:
        new_reps = 0
        new_interval = 1.0

    new_ef = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = max(1.3, new_ef)

    return ReviewResult(
        repetitions=new_reps,
        interval=round(new_interval, 2),
        ease_factor=round(new_ef, 2),
        due_at=review_time + timedelta(days=new_interval),
    )


def rating_to_quality(rating: str) -> int:
    return RATING_TO_QUALITY.get(rating.lower(), 3)
