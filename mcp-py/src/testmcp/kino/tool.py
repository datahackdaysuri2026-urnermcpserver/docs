import json
from typing import Optional
from difflib import SequenceMatcher

from pydantic import BaseModel
from pathlib import Path

from datetime import datetime

from testmcp.base import UriMCPTool, register_as_resource, register_as_tool


import os

from testmcp.kino.model import CinemaProgram

class KinoResponse(BaseModel):
    description: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    info_url : Optional[str] = None



class KinoTool(UriMCPTool):

    def __init__(self):
        """ Initialize the KinoTool with the MCP server instance and load the cinema program data."""
        # Load the cinema program data from the JSON file
        #TODO: In a real application, this data would likely come from a database or external API rather than a static file.

        data_dir = Path(os.environ.get("DATA_PATH", "../data"))
        #data_dir = Path("../data")

        with open(data_dir / "cinema_leuzinger.json", "r", encoding='utf-8') as f:
            events = json.load(f)
        
        self.eventfeed = CinemaProgram.model_validate(events)

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
    async def get_kinoprogramm(self, keywords: Optional[list[str] | str] = None, date: Optional[str] = None) -> list[KinoResponse]:
        """
        Get kino program in Altdorf. Define specific search keywords or search for a specific date.
        """
        print(f"get_kinoprogamm tool called with keywords={keywords}, date={date}")       
        
        # Date can be in the format "YYYY-MM-DD" or "YYYY-MM" or "YYYY" or "März 2026" or "März" or "2026"
        parsed_date = self._parse_date(date) if date else None
        normalized_keywords = self._normalize_keywords(keywords)
                
        events = await self._search_events(keywords=normalized_keywords, date=parsed_date)
        print(f"get_kinoprogamm tool returning {len(events)} events")       
        
        return events


    def _fuzzy_match(self, text1: str, text2: str) -> float:
        """Calculate fuzzy match score between two strings (0.0 to 1.0)."""
        if not text1 or not text2:
            return 0.0
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    async def _search_events(self, keywords: Optional[list[str]] = None, date: Optional[str] = None, place: Optional[str] = None) -> list[KinoResponse]:
        """Search for events using fuzzy matching with ranking based on keywords, date, and place.
        Args:
            keywords: List of keywords to match against event descriptions.
            date: Date string to match against event dates. Can be in various formats (e.g., "2026-03-15", "März 2026").
            place: Place string to match against event locations.
        """

        events = self.eventfeed.data
        scored_events: list[tuple[float, KinoResponse]] = []

        for ev in events:
            desc = ev.titel
            ev_date = str(ev.datum)
            ev_time = str(ev.zeit)

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

            # Score date match
            if date and ev_date:
                date_score = self._fuzzy_match(date, ev_date)
                score += date_score * 0.2  # 20% weight on date

            # Only include events with non-zero score
            if score > 0:
                scored_events.append((score, KinoResponse(description=desc, date=ev_date, time=ev_time, info_url=None)))

        # Sort by score in descending order
        scored_events.sort(key=lambda x: x[0], reverse=True)

        # Extract just the KinoResponse objects
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
        return datetime.today().date().strftime("%d.%m.%Y")  # Default to today's date if parsing fails
