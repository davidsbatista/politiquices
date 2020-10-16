from dataclasses import dataclass


@dataclass
class OfficePosition:
    start: str
    end: str
    position: str


@dataclass
class PoliticalParty:
    name: str
    image_url: str