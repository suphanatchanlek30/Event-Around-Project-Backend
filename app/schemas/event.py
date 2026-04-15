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


class EventCreateRequest(BaseModel):
    title: str
    description: str | None = None
    short_description: str | None = Field(None, alias="shortDescription")
    location_name: str = Field(..., alias="locationName")
    latitude: float
    longitude: float
    start_time: datetime = Field(..., alias="startTime")
    end_time: datetime = Field(..., alias="endTime")
    category_id: int = Field(..., alias="categoryId")
    cover_image_url: str | None = Field(None, alias="coverImageUrl")
    status: str | None = Field(default="DRAFT")

    model_config = {"populate_by_name": True}


class EventImportItem(BaseModel):
    title: str
    description: str | None = None
    short_description: str | None = Field(None, alias="shortDescription")
    location_name: str = Field(..., alias="locationName")
    latitude: float
    longitude: float
    start_time: datetime = Field(..., alias="startTime")
    end_time: datetime = Field(..., alias="endTime")
    category_id: int = Field(..., alias="categoryId")
    cover_image_url: str | None = Field(None, alias="coverImageUrl")
    status: str | None = None

    model_config = {"populate_by_name": True}


class EventImportRequest(BaseModel):
    events: list[EventImportItem]

    model_config = {"populate_by_name": True}


class EventUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    short_description: str | None = Field(None, alias="shortDescription")
    location_name: str | None = Field(None, alias="locationName")
    latitude: float | None = None
    longitude: float | None = None
    start_time: datetime | None = Field(None, alias="startTime")
    end_time: datetime | None = Field(None, alias="endTime")
    category_id: int | None = Field(None, alias="categoryId")
    cover_image_url: str | None = Field(None, alias="coverImageUrl")

    model_config = {"populate_by_name": True}


class EventCancelRequest(BaseModel):
    reason: str

    model_config = {"populate_by_name": True}


class NearbyEventResponse(BaseModel):
    event_id: int = Field(..., alias="eventId")
    title: str
    location_name: str = Field(..., alias="locationName")
    latitude: float
    longitude: float
    distance_km: float = Field(..., alias="distanceKm")
    start_time: datetime = Field(..., alias="startTime")
    end_time: datetime = Field(..., alias="endTime")
    category: EventCategoryResponse

    model_config = {"populate_by_name": True}


class MapEventResponse(BaseModel):
    event_id: int = Field(..., alias="eventId")
    title: str
    latitude: float
    longitude: float
    location_name: str = Field(..., alias="locationName")
    distance_km: float = Field(..., alias="distanceKm")
    start_time: datetime = Field(..., alias="startTime")

    model_config = {"populate_by_name": True}


class SaveEventRequest(BaseModel):
    event_id: int = Field(..., alias="eventId", ge=1)

    model_config = {"populate_by_name": True}
