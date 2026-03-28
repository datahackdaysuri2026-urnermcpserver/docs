import json
from typing import Optional
from difflib import SequenceMatcher
from datetime import date, datetime

from pydantic import BaseModel
from pathlib import Path

from testmcp.base import UriMCPTool, register_as_resource, register_as_tool

from testmcp.events.model import EventFeed

import os

class EventResponse(BaseModel):
    description: Optional[str] = None
    date: Optional[str] = None
    #time: Optional[str] = None
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
            date: Date string to match against event dates. Can be a single day in format "15.03.2026" or a month in format "März 2026".
            place: Place string to match against event locations im Kanton Uri. If place is empty: return all events regardless of place.
        """
        print(f"get_events tool called with keywords={keywords}, date={date}, place={place}")       
        #await ctx.info(f"get_events tool called with keywords={keywords}, date={date}, place={place}")

        # Date can be in the format "YYYY-MM-DD" or "YYYY-MM" or "YYYY" or "März 2026" or "März" or "2026"
        parsed_date = self._parse_date(date) if date else None
        normalized_keywords = self._normalize_keywords(keywords)
                
        events = await self._search_events(keywords=normalized_keywords, date=parsed_date, place=place)
        print(f"get_events tool returning {len(events)} events")       
        
        return events


    def _fuzzy_match(self, text1: str, text2: str) -> float:
        """Calculate fuzzy match score between two strings (0.0 to 1.0)."""
        if not text1 or not text2:
            return 0.0
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def _normalize_place(self, place: Optional[str]) -> Optional[str]:
        """Normalize place input for strict comparisons."""
        if not place:
            return None
        normalized = place.strip().lower()
        return normalized if normalized else None

    async def _search_events(self, keywords: Optional[list[str]] = None, date: Optional[date] = None, place: Optional[str] = None) -> list[EventResponse]:
        """Search for events with strict date/place filters and fuzzy keyword ranking.
        Args:
            keywords: List of keywords to match against event descriptions.
            date: Event date that must match exactly after parsing.
            place: Event place that must match exactly (case-insensitive).
        """

        events = self.eventfeed.events()

        scored_events: list[tuple[float, EventResponse]] = []
        keyword_threshold = 0.35
        normalized_place = self._normalize_place(place)

        for ev in events:
            details = ev.offerDetail[0] if ev.offerDetail else None

            desc = details.shortDescription if details else None
            
            ev_dates = ev.schedules.dates if ev.schedules and ev.schedules.dates else []
            ev_start_dates = [d.startDate for d in ev_dates]  # Sort by start date
            #ev_start_times = [d.startTime for d in ev_dates]  # Sort by start date
            
            
            ev_place = ev.address.city if ev.address else None
            info_url = details.detailUrl if details else None
            organisation = ev.bpName if ev.bpName else None

            # Strict date filter            
            has_matching_date = False
            for ev_date in ev_start_dates:
                if date and ev_date == date:
                    has_matching_date = True
                    break
            if date and not has_matching_date:
                continue
            
            # Strict place filter (case-insensitive)
            if normalized_place:
                if not ev_place or self._normalize_place(ev_place) != normalized_place:
                    continue

            score = 1.0

            # Fuzzy keywords only influence ranking and inclusion when provided.
            if keywords:
                keyword_scores = []
                searchable_fields = [desc or "", organisation or ""]
                for keyword in keywords:
                    best_match = max((self._fuzzy_match(keyword, field) for field in searchable_fields), default=0.0)
                    keyword_scores.append(best_match)

                avg_keyword_score = sum(keyword_scores) / len(keyword_scores) if keyword_scores else 0.0
                if avg_keyword_score < keyword_threshold:
                    continue
                score = avg_keyword_score

            scored_events.append((score, EventResponse(description=desc, date=ev_date.isoformat() if ev_date else None, place=ev_place, info_url=info_url, organisation=organisation)))

        # Sort by score in descending order
        scored_events.sort(key=lambda x: x[0], reverse=True)

        # Extract just the EventResponse objects
        response = [event for _, event in scored_events]

        return response

    def _parse_date(self, date_str: str) -> date:
        """Parse a date string in various formats and return a date instance."""
        date_formats = ["%Y-%m-%d", "%d.%m.%Y", "%d.%m", "%d %B", "%Y", "%B %Y", "%B"]
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return datetime.today().date()  # Default to today
