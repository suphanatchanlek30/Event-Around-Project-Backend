from datetime import datetime

from pydantic import BaseModel, Field


class EventCategoryResponse(BaseModel):
    category_id: int = Field(..., alias="categoryId")
    name: str


class OrganizerResponse(BaseModel):
    user_id: int = Field(..., alias="userId")
    full_name: str = Field(..., alias="fullName")


class EventResponseData(BaseModel):
    event_id: int = Field(..., alias="eventId")
    title: str
    location_name: str = Field(..., alias="locationName")
    start_time: datetime = Field(..., alias="startTime")
    end_time: datetime = Field(..., alias="endTime")
    status: str
    category: EventCategoryResponse
    organizer: OrganizerResponse

    model_config = {"populate_by_name": True}
