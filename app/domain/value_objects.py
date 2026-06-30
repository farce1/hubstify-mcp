from datetime import date

from pydantic import BaseModel, model_validator


class Duration(BaseModel):
    seconds: int

    @classmethod
    def from_hours(cls, hours: float) -> "Duration":
        return cls(seconds=round(hours * 3600))

    @property
    def hours(self) -> float:
        return self.seconds / 3600

    @property
    def human(self) -> str:
        h, rem = divmod(self.seconds, 3600)
        m = rem // 60
        parts = [f"{h}h"] if h else []
        if m or not parts:
            parts.append(f"{m}m")
        return " ".join(parts)


class DateRange(BaseModel):
    start: date
    stop: date

    @model_validator(mode="after")
    def _check_order(self) -> "DateRange":
        if self.start > self.stop:
            raise ValueError("start must not be after stop")
        return self

    @property
    def days(self) -> int:
        return (self.stop - self.start).days + 1
