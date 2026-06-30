from datetime import date

import pytest
from pydantic import ValidationError

from app.domain.value_objects import DateRange, Duration


class TestDuration:
    def test_from_hours_converts_to_seconds(self):
        assert Duration.from_hours(2).seconds == 7200

    def test_from_hours_rounds_to_nearest_second(self):
        assert Duration.from_hours(0.5).seconds == 1800

    def test_hours_property(self):
        assert Duration(seconds=7200).hours == 2.0

    @pytest.mark.parametrize(
        ("seconds", "expected"),
        [
            (9000, "2h 30m"),
            (3600, "1h"),
            (1800, "30m"),
            (0, "0m"),
            (90, "1m"),
        ],
    )
    def test_human_readable(self, seconds, expected):
        assert Duration(seconds=seconds).human == expected


class TestDateRange:
    def test_single_day_spans_one_day(self):
        r = DateRange(start=date(2026, 6, 30), stop=date(2026, 6, 30))
        assert r.days == 1

    def test_week_spans_seven_days(self):
        r = DateRange(start=date(2026, 6, 1), stop=date(2026, 6, 7))
        assert r.days == 7

    def test_start_after_stop_is_rejected(self):
        with pytest.raises(ValidationError):
            DateRange(start=date(2026, 6, 7), stop=date(2026, 6, 1))
