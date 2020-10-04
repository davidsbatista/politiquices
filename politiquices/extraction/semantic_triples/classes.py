from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Set, Optional


@dataclass
class Person:
    name: str
    also_known_as: Set[str]
    power_id: Optional[str]
    wikidata_id: str


@dataclass
class Article:
    url: str
    title: str
    source: Optional[str]
    date: Optional[datetime]
    crawled_date: Optional[datetime]


@dataclass
class RelationshipType(Enum):
    ent1_opposes_ent2 = 1
    ent2_opposes_ent1 = 2
    ent1_supports_ent2 = 3
    ent2_supports_ent1 = 4
    both_agree = 5
    both_disagree = 6
    other = 7


@dataclass
class Relationship:
    url: str
    rel_type: str
    rel_score: float
    ent1: Person
    ent2: Person
