from datetime import date

from pydantic import BaseModel, model_validator


class DateRange(BaseModel):
    start: date
    stop: date

    @model_validator(mode="after")
    def _check_order(self) -> "DateRange":
        if self.start > self.stop:
            raise ValueError("start must not be after stop")
        return self
