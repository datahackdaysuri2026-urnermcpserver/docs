import json
from typing import Optional
from difflib import SequenceMatcher

from pydantic import BaseModel
from pathlib import Path

from datetime import datetime

from testmcp.base import UriMCPTool, register_as_resource, register_as_tool


from testmcp.events.model import EventFeed

import os

class EventResponse(BaseModel):
    description: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    place: Optional[str] = None
    info_url : Optional[str] = None
    organisation: Optional[str] = None



class EventsTool(UriMCPTool):

    def __init__(self):
        """ Initialize the EventsTool with the MCP server instance and load the event data."""
        # Load the event data from the JSON file
        #TODO: In a real application, this data would likely come from a database or external API rather than a static file.

        data_dir = Path(os.environ.get("DATA_PATH", "../data"))
        #data_dir = Path("../data")

        with open(data_dir / "uri_veranstaltungskalender.json", "r", encoding='utf-8') as f:
            events = json.load(f)
        
        self.eventfeed = EventFeed.model_validate(events)

    def _normalize_keywords(self, keywords: Optional[list[str] | str]) -> list[str]:
        """Accept list or string input and return a clean keyword list."""
        if keywords is None:
            return []

        if isinstance(keywords, str):
            normalized = keywords.strip()
            if not normalized:
                return []
            # Allow comma-separated or whitespace-separated keyword strings.
            raw_parts = normalized.replace(",", " ").split()
            return [part for part in raw_parts if part]

        return [kw.strip() for kw in keywords if isinstance(kw, str) and kw.strip()]


    @register_as_tool()
    async def get_events(self, keywords: Optional[list[str] | str] = None, date: Optional[str] = None, place: Optional[str] = None) -> list[EventResponse]:
        """
        Get events that contain specific keywords for a specific date and place.

                Args:
            keywords: List of keywords to match against event descriptions.
            date: Date string to match against event dates. Can be in various formats (e.g., "2026-03-15", "März 2026"). "%d.%m.%Y", "%d.%m", "%d %B", "%Y", "%B %Y", "%B"
            place: Place string to match against event locations im Kanton Uri.
        
        """
        print(f"get_events tool called with keywords={keywords}, date={date}, place={place}")       
        #await ctx.info(f"get_events tool called with keywords={keywords}, date={date}, place={place}")

        # Date can be in the format "YYYY-MM-DD" or "YYYY-MM" or "YYYY" or "März 2026" or "März" or "2026"
        parsed_date = self._parse_date(date) if date else None
        normalized_keywords = self._normalize_keywords(keywords)
                
        events = await self._search_events(keywords=normalized_keywords, date=parsed_date, place=place)
        print(f"get_events tool returning {len(events)} events")       
        
        return events

    

    #@register_as_resource("data://events")
    async def events(self) -> list[EventResponse]:
        """Return all events as a list of EventResponse objects."""
        #ctx = get_context()
        #await ctx.info("Fetching events resource...")
        
        events = self.eventfeed.events()

        response = list()
        for ev in events:
            details = ev.offerDetail[0] if ev.offerDetail else None

            desc = details.shortDescription if details else None
            ev_date = ev.schedules.dates[0].startDate if ev.schedules and ev.schedules.dates else None
            ev_time = ev.schedules.dates[0].startTime if ev.schedules and ev.schedules.dates else None
            ev_place = ev.address.city if ev.address else None
            info_url = details.detailUrl if details else None
            organisation = ev.bpName if ev.bpName else None

            response.append(EventResponse(description=desc, date=ev_date, time=ev_time, place=ev_place, info_url=info_url, organisation=organisation))
        
        return response


    def _fuzzy_match(self, text1: str, text2: str) -> float:
        """Calculate fuzzy match score between two strings (0.0 to 1.0)."""
        if not text1 or not text2:
            return 0.0
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    async def _search_events(self, keywords: Optional[list[str]] = None, date: Optional[str] = None, place: Optional[str] = None) -> list[EventResponse]:
        """Search for events using fuzzy matching with ranking based on keywords, date, and place.
        Args:
            keywords: List of keywords to match against event descriptions.
            date: Date string to match against event dates. Can be in various formats (e.g., "2026-03-15", "März 2026"). "%d.%m.%Y", "%d.%m", "%d %B", "%Y", "%B %Y", "%B"
            place: Place string to match against event locations.
        """

        events = self.eventfeed.events()
        scored_events: list[tuple[float, EventResponse]] = []

        for ev in events:
            details = ev.offerDetail[0] if ev.offerDetail else None

            desc = details.shortDescription if details else None
            ev_date = ev.schedules.dates[0].startDate if ev.schedules and ev.schedules.dates else None
            ev_time = ev.schedules.dates[0].startTime if ev.schedules and ev.schedules.dates else None
            ev_place = ev.address.city if ev.address else None
            info_url = details.detailUrl if details else None
            organisation = ev.bpName if ev.bpName else None

            score = 0.0

            # Score keywords matches
            if keywords:
                keyword_scores = []
                for keyword in keywords:
                    if desc:
                        match_score = self._fuzzy_match(keyword, desc)
                        keyword_scores.append(match_score)
                    else:
                        keyword_scores.append(0.0)
                # Use the max score for each keyword, then average
                if keyword_scores:
                    score += sum(keyword_scores) / len(keyword_scores) * 0.6  # 60% weight on keywords

            # Score place match
            if place and ev_place:
                place_score = self._fuzzy_match(place, ev_place)
                score += place_score * 0.2  # 20% weight on place

            # Score date match
            if date and ev_date:
                date_score = self._fuzzy_match(date, ev_date)
                score += date_score * 0.2  # 20% weight on date

            # Only include events with non-zero score
            if score > 0:
                scored_events.append((score, EventResponse(description=desc, date=ev_date, time=ev_time, place=ev_place, info_url=info_url, organisation=organisation)))

        # Sort by score in descending order
        scored_events.sort(key=lambda x: x[0], reverse=True)

        # Extract just the EventResponse objects
        response = [event for _, event in scored_events]

        return response

    def _parse_date(self, date_str: str) -> str:
        """ Parse a date string in various formats and return a formatted date string."""
        target_format = "%d.%m.%Y"  # Desired output format
        date_formats = ["%d.%m.%Y", "%d.%m", "%d %B", "%Y", "%B %Y", "%B"] # Add more formats as needed
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date().strftime(target_format)
            except ValueError:
                continue
        return datetime.today().date().strftime("%m.%Y")  # Default to today's Month and year if parsing fails
