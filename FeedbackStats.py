"""
# FeedbackStats.py
# Encapsulated statistics tracking for the customer feedback kiosk.
# Tracks vote tallies, calculates satisfaction percentages, and evaluates alarm thresholds.
# Author: Lushana3
"""

from Log import *

class FeedbackStats:
    """
    Encapsulates visitor feedback vote tallies and calculates satisfaction metrics.

    Maintains private counters for happy, neutral, and unhappy votes. Provides methods
    to compute satisfaction score percentages, map the score to an 8-LED light strip level,
    and determine whether the manager alarm threshold (minimum 5 votes and score < 30%)
    has been breached.

    Parameters:
    ----------
    None

    Examples:
    ---------
    1. Tracking votes and checking percentage:
       stats = FeedbackStats()
       stats.add_happy()
       stats.add_neutral()
       score = stats.calculate_percentage()  # 75.0%

    2. Checking alarm condition:
       if stats.is_low():
           Log.i("Feedback dropped below 30% after at least 5 votes!")
    """

    def __init__(self):
        """
        Initialize all private feedback counters to zero.
        """
        self._happy_count = 0
        self._neutral_count = 0
        self._unhappy_count = 0
        Log.i("FeedbackStats initialized with 0 votes")

    def add_happy(self):
        """
        Record a positive / happy visitor vote.
        """
        self._happy_count += 1
        Log.i(f"Happy vote recorded. Happy total: {self._happy_count}")

    def add_neutral(self):
        """
        Record a neutral visitor vote.
        """
        self._neutral_count += 1
        Log.i(f"Neutral vote recorded. Neutral total: {self._neutral_count}")

    def add_unhappy(self):
        """
        Record a negative / unhappy visitor vote.
        """
        self._unhappy_count += 1
        Log.i(f"Unhappy vote recorded. Unhappy total: {self._unhappy_count}")

    def get_total_count(self) -> int:
        """
        Calculate and return the total number of votes recorded.

        Returns:
        -------
        int
            Total vote count across happy, neutral, and unhappy ratings.
        """
        return self._happy_count + self._neutral_count + self._unhappy_count

    def calculate_percentage(self) -> float:
        """
        Calculate the weighted visitor satisfaction percentage.

        Formula: ((happy + 0.5 * neutral) / total) * 100.
        Returns 100.0 if no votes have been recorded yet.

        Returns:
        -------
        float
            Satisfaction percentage between 0.0 and 100.0.
        """
        total = self.get_total_count()
        if total == 0:
            return 100.0
        score = ((self._happy_count + 0.5 * self._neutral_count) / total) * 100.0
        return score

    def get_light_level(self) -> int:
        """
        Translate the current satisfaction score to an 8-LED light strip level.

        Returns:
        -------
        int
            Number of LEDs to illuminate from 0 to 8.
        """
        pct = self.calculate_percentage()
        level = round((pct / 100.0) * 8)
        return max(0, min(8, level))

    def is_low(self) -> bool:
        """
        Determine if the manager alarm should be triggered.

        The alarm condition requires at least 5 total votes and a satisfaction
        percentage below 30.0%.

        Returns:
        -------
        bool
            True if total votes >= 5 and satisfaction < 30.0%, otherwise False.
        """
        return self.get_total_count() >= 5 and self.calculate_percentage() < 30.0

    def reset(self):
        """
        Reset all feedback counters to zero.
        """
        self._happy_count = 0
        self._neutral_count = 0
        self._unhappy_count = 0
        Log.i("FeedbackStats reset to 0 votes")


if __name__ == "__main__":
    Log.i("Testing FeedbackStats...")

    stats = FeedbackStats()
    assert stats.get_total_count() == 0, "Initial count should be 0"
    assert stats.calculate_percentage() == 100.0, "Zero votes should return 100.0%"
    assert stats.get_light_level() == 8, "100% should light 8 LEDs"
    assert not stats.is_low(), "Zero votes should not trigger alarm"

    # Test vote addition and weighted percentage
    stats.add_happy()    # 1.0
    stats.add_neutral()  # 0.5
    stats.add_unhappy()  # 0.0
    # Total = 3, score = (1.5 / 3) * 100 = 50.0%
    assert stats.get_total_count() == 3, f"Expected 3, got {stats.get_total_count()}"
    pct = stats.calculate_percentage()
    assert abs(pct - 50.0) < 0.001, f"Expected 50.0%, got {pct}"
    assert stats.get_light_level() == 4, f"Expected 4 LEDs, got {stats.get_light_level()}"
    assert not stats.is_low(), "Total < 5 should not trigger alarm"

    # Test threshold gate: 4 unhappy votes (total 4, score 0%)
    stats.reset()
    for _ in range(4):
        stats.add_unhappy()
    assert stats.get_total_count() == 4
    assert stats.calculate_percentage() == 0.0
    assert not stats.is_low(), "Alarm must not trigger before 5 votes"

    # 5th unhappy vote -> total 5, score 0% < 30% -> is_low() should be True
    stats.add_unhappy()
    assert stats.get_total_count() == 5
    assert stats.calculate_percentage() == 0.0
    assert stats.is_low(), "Alarm should trigger with 5 unhappy votes"
    assert stats.get_light_level() == 0, f"Expected 0 LEDs, got {stats.get_light_level()}"

    # Reset
    stats.reset()
    assert stats.get_total_count() == 0
    assert not stats.is_low()

    Log.i("Testing complete - all checks passed")
