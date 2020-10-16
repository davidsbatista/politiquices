from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List


@dataclass
class OfficePosition:
    start: str
    end: str
    position: str


@dataclass
class PoliticalParty:
    name: str
    image_url: str


@dataclass
class Person:
    wiki_id: str
    name: str
    image_url: str
    parties: List[PoliticalParty]
    positions: List[OfficePosition]


@dataclass
class RelationshipType(Enum):
    # ToDo: add more
    FIRST = "ent1_opposes_ent2"
    SECOND = "ent2_opposes_ent1"
    THREE = "ent1_supports_ent2"
    FOUR = "ent2_supports_ent1"


@dataclass
class Relationship:
    rel_type: RelationshipType
    rel_score: float
    article_url: str
    article_date: datetime
    ent1: Person
    ent2: Person
