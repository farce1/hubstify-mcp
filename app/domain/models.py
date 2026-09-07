from datetime import date

from pydantic import BaseModel, ConfigDict, model_validator


class HubstaffModel(BaseModel):
    """Base for models mapped from Hubstaff API responses; ignores unmapped fields."""

    model_config = ConfigDict(extra="ignore")


class User(HubstaffModel):
    id: int
    name: str
    email: str | None = None
    time_zone: str | None = None


class Organization(HubstaffModel):
    id: int
    name: str


class OrganizationMember(HubstaffModel):
    user_id: int
    membership_role: str | None = None
    user: User | None = None


class Team(HubstaffModel):
    id: int
    name: str


class Project(HubstaffModel):
    id: int
    name: str
    status: str | None = None
    billable: bool | None = None


class Task(HubstaffModel):
    id: int
    summary: str
    status: str | None = None
    project_id: int | None = None


class DailyActivity(HubstaffModel):
    """Per-day aggregated tracked time."""

    date: date
    project_id: int | None = None
    tracked: int = 0


class DateRange(BaseModel):
    start: date
    stop: date

    @model_validator(mode="after")
    def _check_order(self) -> "DateRange":
        if self.start > self.stop:
            raise ValueError("start must not be after stop")
        return self
