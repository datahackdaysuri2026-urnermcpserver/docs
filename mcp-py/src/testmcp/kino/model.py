from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Screening(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    datum: date = Field(alias="Datum")
    zeit: time = Field(alias="Zeit")
    titel: str = Field(alias="Titel")
    typ: str = Field(alias="Typ")
    sprache: str = Field(alias="Sprache")
    dauer: str = Field(alias="Dauer")

    @field_validator("dauer", mode="before")
    @classmethod
    def normalise_dauer(cls, v: str) -> str:
        """Strip trailing dot so '104 Min.' and '104 Min' are stored identically."""
        return v.rstrip(".")

    @property
    def duration_minutes(self) -> Optional[int]:
        """Return duration as an integer number of minutes, or None if unparseable."""
        parts = self.dauer.split()
        try:
            return int(parts[0])
        except (IndexError, ValueError):
            return None


class CinemaProgram(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    scraper_name: str
    execution_time: datetime
    success: bool
    record_count: int
    data: list[Screening]

    def screenings_on(self, day: date) -> list[Screening]:
        """Return all screenings for a specific date."""
        return [s for s in self.data if s.datum == day]

    def screenings_for_title(self, title: str) -> list[Screening]:
        """Return all screenings whose title contains the given string (case-insensitive)."""
        needle = title.lower()
        return [s for s in self.data if needle in s.titel.lower()]
