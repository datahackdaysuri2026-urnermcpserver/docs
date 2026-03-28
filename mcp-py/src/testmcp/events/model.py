from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class TagRef(BaseModel):
    id: int
    name: str


class ClassificationName(BaseModel):
    language: str
    name: str


class TagName(BaseModel):
    language: str
    name: str
    subcategoryName: Optional[str] = None


class ClassificationTag(BaseModel):
    id: int
    name: str
    subcategoryId: Optional[int] = None
    subcategoryName: Optional[str] = None
    tagNames: list[TagName] = []


class Classification(BaseModel):
    id: int
    name: str
    classificationNames: list[ClassificationName] = []
    tags: list[ClassificationTag] = []


class ScheduleDate(BaseModel):
    startDate: str
    endDate: str
    startTime: Optional[str] = None
    endTime: Optional[str] = None


class Schedules(BaseModel):
    dates: list[ScheduleDate] = []


class ImageSize(BaseModel):
    label: str
    url: str
    width: Optional[int] = None
    height: Optional[int] = None
    dpi: Optional[int] = None


class Image(BaseModel):
    id: int
    url: str
    thumbnailUrl: Optional[str] = None
    description: Optional[str] = None
    size: list[ImageSize] = []


class OfferDetail(BaseModel):
    id: int
    languageCode: str
    title: str
    shortDescription: Optional[str] = None
    longDescription: Optional[str] = None
    priceInformation: Optional[str] = None
    homepage: Optional[str] = None
    detailUrl: Optional[str] = None
    images: list[Image] = []


class Address(BaseModel):
    id: int
    cityId: Optional[int] = None
    ownerBpId: Optional[int] = None
    company: Optional[str] = None
    street: Optional[str] = None
    zip: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    lastUpdateDate: Optional[str] = None
    venueName: Optional[str] = None


class Contact(BaseModel):
    id: Optional[int] = None
    noContactData: Optional[bool] = None
    name: Optional[str] = None
    address_line_1: Optional[str] = Field(default=None, alias="address_1")
    zip: Optional[str] = None
    city: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    lastUpdateDate: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class Event(BaseModel):
    id: int
    bpId: Optional[int] = None
    bpName: Optional[str] = None
    createDate: Optional[str] = None
    lastUpdateDate: Optional[str] = None
    webcode: Optional[str] = None

    offerDetail: list[OfferDetail] = []
    address: Optional[Address] = None
    contact: Optional[Contact] = None
    schedules: Optional[Schedules] = None
    classifications: list[Classification] = []


class GroupSet(BaseModel):
    count: int
    offers: list[Event] = []


class WhereFilter(BaseModel):
    locationTags: list[TagRef] = []


class WhenFilter(BaseModel):
    dateOption: Optional[str] = None


class WhatFilter(BaseModel):
    kindTags: list[TagRef] = []


class SearchCriteria(BaseModel):
    where: Optional[WhereFilter] = None
    when: Optional[WhenFilter] = None
    what: Optional[WhatFilter] = None


class Header(BaseModel):
    createDate: Optional[str] = None
    searchCriteria: Optional[SearchCriteria] = None
    count: Optional[int] = None


class EventFeed(BaseModel):
    header: Header
    groupSet: list[GroupSet]

    def events(self) -> list[Event]:
        events: list[Event] = []
        for group in self.groupSet:
            events.extend(group.offers)
        return events