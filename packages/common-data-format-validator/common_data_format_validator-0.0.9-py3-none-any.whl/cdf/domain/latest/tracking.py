# Auto-generated from JSON Schema v0.2.1
# Do not edit manually - run generate_latest_domain.py


from __future__ import annotations

from typing import List, Literal, TypedDict

from typing_extensions import NotRequired


class Match(TypedDict):
    id: str


class Ball(TypedDict):
    x: float
    y: float
    z: float


class Referee(TypedDict):
    id: str
    x: float
    y: float
    z: NotRequired[float]
    vel: NotRequired[float]
    acc: NotRequired[float]
    lat: NotRequired[float]
    long: NotRequired[float]
    is_visible: NotRequired[bool]
    minutes_played: NotRequired[float]


class Event(TypedDict):
    name: NotRequired[str]


class Tracking(TypedDict):
    name: NotRequired[str]


class Vendor(TypedDict):
    event: NotRequired[Event]
    tracking: NotRequired[Tracking]


class Player(TypedDict):
    id: str
    x: float
    y: float
    z: NotRequired[float]
    vel: NotRequired[float]
    acc: NotRequired[float]
    lat: NotRequired[float]
    long: NotRequired[float]
    is_visible: NotRequired[bool]
    minutes_played: NotRequired[float]


class Team(TypedDict):
    id: NotRequired[str]
    players: NotRequired[List[Player]]
    name: NotRequired[str]
    jersey_colour: NotRequired[str]
    formation: NotRequired[str]


class Teams(TypedDict):
    home: Team
    away: Team


class CdfTrackingDataSchema(TypedDict):
    frame_id: int
    timestamp: str
    period: Literal[
        "first_half",
        "second_half",
        "first_half_extratime",
        "second_half_extratime",
        "shootout",
    ]
    match: Match
    teams: Teams
    ball: Ball
    referees: NotRequired[List[Referee]]
    ball_status: NotRequired[bool]
    ball_poss_team_id: NotRequired[str]
    ball_poss_status: NotRequired[str]
    vendor: NotRequired[Vendor]
