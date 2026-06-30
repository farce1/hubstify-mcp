from pydantic import BaseModel, ConfigDict


class HubstaffModel(BaseModel):
    """Base for models mapped from Hubstaff API responses; ignores unmapped fields."""

    model_config = ConfigDict(extra="ignore")
