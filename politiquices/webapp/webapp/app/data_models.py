from dataclasses import dataclass
from typing import List, Optional


@dataclass
class OfficePosition:
    position: str


@dataclass
class PoliticalParty:
    wiki_id: str
    name: str
    image_url: str


@dataclass
class Person:
    wiki_id: str
    name: Optional[str] = None
    nr_articles: Optional[int] = None
    image_url: Optional[str] = None
    parties: Optional[List[PoliticalParty]] = None
    positions: Optional[List[str]] = None
    education: Optional[List[str]] = None
    occupations: Optional[List[str]] = None
