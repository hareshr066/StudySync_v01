"""Tests for SM-2 algorithm."""

import pytest
from datetime import datetime, timezone, timedelta
from app.services.sm2 import calculate_sm2, rating_to_quality, RATING_TO_QUALITY


class TestRatingToQuality:
    def test_again(self):
        assert rating_to_quality("again") == 0

    def test_hard(self):
        assert rating_to_quality("hard") == 2

    def test_good(self):
        assert rating_to_quality("good") == 3

    def test_easy(self):
        assert rating_to_quality("easy") == 5

    def test_case_insensitive(self):
        assert rating_to_quality("GOOD") == 3

    def test_unknown_defaults(self):
        assert rating_to_quality("unknown") == 3


class TestSM2Algorithm:
    """Test SM-2 calculation logic."""

    def test_first_good_review(self):
        """First successful review should set interval to 1 day."""
        now = datetime(2024, 1, 1, tzinfo=timezone.utc)
        result = calculate_sm2(quality=3, repetitions=0, interval=0, ease_factor=2.5, review_time=now)
        assert result.repetitions == 1
        assert result.interval == 1.0
        assert result.due_at == now + timedelta(days=1)

    def test_second_good_review(self):
        """Second successful review should set interval to 6 days."""
        now = datetime(2024, 1, 2, tzinfo=timezone.utc)
        result = calculate_sm2(quality=3, repetitions=1, interval=1, ease_factor=2.5, review_time=now)
        assert result.repetitions == 2
        assert result.interval == 6.0
        assert result.due_at == now + timedelta(days=6)

    def test_third_good_review(self):
        """Third+ successful review uses interval * ease_factor."""
        now = datetime(2024, 1, 8, tzinfo=timezone.utc)
        result = calculate_sm2(quality=3, repetitions=2, interval=6, ease_factor=2.5, review_time=now)
        assert result.repetitions == 3
        assert result.interval == 15.0  # 6 * 2.5
        assert result.due_at == now + timedelta(days=15)

    def test_again_resets(self):
        """Failed review (again) should reset repetitions and interval."""
        result = calculate_sm2(quality=0, repetitions=5, interval=30, ease_factor=2.5)
        assert result.repetitions == 0
        assert result.interval == 1.0

    def test_hard_resets(self):
        """Hard (quality 2) should also reset since 2 < 3."""
        result = calculate_sm2(quality=2, repetitions=3, interval=15, ease_factor=2.5)
        assert result.repetitions == 0
        assert result.interval == 1.0

    def test_easy_increases_ease(self):
        """Easy (quality 5) should increase ease factor."""
        result = calculate_sm2(quality=5, repetitions=0, interval=0, ease_factor=2.5)
        assert result.ease_factor == 2.6

    def test_again_decreases_ease(self):
        """Again (quality 0) should decrease ease factor."""
        result = calculate_sm2(quality=0, repetitions=0, interval=0, ease_factor=2.5)
        assert result.ease_factor < 2.5

    def test_ease_factor_minimum(self):
        """Ease factor should never go below 1.3."""
        result = calculate_sm2(quality=0, repetitions=0, interval=0, ease_factor=1.3)
        assert result.ease_factor >= 1.3

    def test_quality_clamped(self):
        """Quality should be clamped to 0-5 range."""
        result = calculate_sm2(quality=10, repetitions=0, interval=0, ease_factor=2.5)
        assert result.repetitions == 1  # quality 5 >= 3, so successful

    def test_due_date_calculation(self):
        """Due date should be review_time + interval days."""
        now = datetime(2024, 6, 15, 10, 0, 0, tzinfo=timezone.utc)
        result = calculate_sm2(quality=3, repetitions=0, interval=0, ease_factor=2.5, review_time=now)
        expected_due = now + timedelta(days=1)
        assert result.due_at == expected_due

    def test_good_ease_factor(self):
        """Good (quality 3) should slightly decrease ease factor."""
        result = calculate_sm2(quality=3, repetitions=0, interval=0, ease_factor=2.5)
        # EF' = 2.5 + (0.1 - (5-3)*(0.08 + (5-3)*0.02)) = 2.5 + (0.1 - 2*(0.08+2*0.02))
        # = 2.5 + (0.1 - 2*0.12) = 2.5 + (0.1 - 0.24) = 2.5 - 0.14 = 2.36
        assert result.ease_factor == 2.36

    def test_progression_sequence(self):
        """Test a realistic study progression."""
        now = datetime(2024, 1, 1, tzinfo=timezone.utc)

        # Day 1: first review - Good
        r1 = calculate_sm2(quality=3, repetitions=0, interval=0, ease_factor=2.5, review_time=now)
        assert r1.interval == 1.0
        assert r1.repetitions == 1

        # Day 2: second review - Good
        r2 = calculate_sm2(quality=3, repetitions=r1.repetitions, interval=r1.interval,
                          ease_factor=r1.ease_factor, review_time=r1.due_at)
        assert r2.interval == 6.0
        assert r2.repetitions == 2

        # Day 8: third review - Easy
        r3 = calculate_sm2(quality=5, repetitions=r2.repetitions, interval=r2.interval,
                          ease_factor=r2.ease_factor, review_time=r2.due_at)
        assert r3.repetitions == 3
        assert r3.interval > r2.interval  # Should grow
