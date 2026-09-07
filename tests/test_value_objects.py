from datetime import date

import pytest
from pydantic import ValidationError

from app.domain.value_objects import DateRange


def test_date_range_allows_a_single_day():
    date_range = DateRange(start=date(2026, 6, 30), stop=date(2026, 6, 30))
    assert date_range.start == date_range.stop


def test_start_after_stop_is_rejected():
    with pytest.raises(ValidationError):
        DateRange(start=date(2026, 6, 7), stop=date(2026, 6, 1))
