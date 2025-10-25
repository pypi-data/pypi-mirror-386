# Auto-generated from JSON Schema v0.2.1
# Do not edit manually - run generate_latest_domain.py


from __future__ import annotations

from typing import List, Literal, Optional, TypedDict

from typing_extensions import NotRequired


class Competition(TypedDict):
    id: str  # Unique identifier for the competition
    name: NotRequired[str]  # Name of the competition
    format: NotRequired[
        str
    ]  # Format of the competition (e.g., 'league_18', 'league_20')
    age_restriction: NotRequired[
        Optional[str]
    ]  # Age restriction for the competition (e.g., 'U18', 'U20')
    type: NotRequired[str]  # Type of competition (e.g., 'youth', 'mens', 'womens')


class Season(TypedDict):
    id: str  # Unique identifier for the season
    name: NotRequired[str]  # Season name (e.g., '2022/23')


class Period(TypedDict):
    period: Literal[
        "first_half",
        "second_half",
        "first_half_extratime",
        "second_half_extratime",
        "shootout",
    ]
    play_direction: Literal[
        "left_right", "right_left"
    ]  # The direction of play for the home team
    time_start: NotRequired[str]  # Start time of the period in UTC
    time_end: NotRequired[str]  # End time of the period in UTC
    frame_id_start: NotRequired[int]  # Frame ID at the start of the period
    frame_id_end: NotRequired[int]  # Frame ID at the start of the period
    left_team_id: NotRequired[
        str
    ]  # Unique team identifier of the team playing on the left side of the pitch in this period. The left_team_id and right_team_id should be the actual, nonstandardized sides.
    right_team_id: NotRequired[
        str
    ]  # Unique team identifier of the team playing on the left side of the pitch in this period. The left_team_id and right_team_id should be the actual, nonstandardized sides.


class Whistle(TypedDict):
    type: str  # Examples of types 'first_half', 'second_half', 'weather_delay', 'health_delay', 'injury_treatment', 'fan_health_delay' etc.
    sub_type: str  # Sub type related to an interruption, for example 'start' or 'end'
    time: str  # The time in UTC of the whistle


class Misc(TypedDict):
    country: NotRequired[str]  # Country where the match is played
    city: NotRequired[str]  # City where the match is played
    percipitation: NotRequired[float]  # Percipitation during the match in millimetres
    is_open_roof: NotRequired[
        bool
    ]  # Indicates if the roof is open (true) or closed (false)


class Match(TypedDict):
    id: str  # Unique identifier for the match
    kickoff_time: str  # Scheduled kickoff time in UTC
    periods: List[Period]
    whistles: List[Whistle]  # Whistles that start and end major periods of play
    round: NotRequired[str]  # Round of the match (e.g. 1, 2, 3, final, semi_final)
    scheduled_kickoff_time: NotRequired[str]  # Scheduled kickoff time in UTC
    local_kickoff_time: NotRequired[str]  # Local kickoff time
    misc: NotRequired[Misc]


class Stadium(TypedDict):
    id: str  # Unique identifier for the stadium
    pitch_length: NotRequired[
        Optional[float]
    ]  # Length of the pitch in metres, null if not available
    pitch_width: NotRequired[
        Optional[float]
    ]  # Width of the pitch in metres, null if not available
    name: NotRequired[str]  # Name of the stadium
    turf: NotRequired[
        str
    ]  # Information on the turf of the pitch (e.g., 'grass', 'natural_reinforced')


class Video(TypedDict):
    perspective: str  # Camera perspective (e.g. in 'stadium', 'broadcast', 'tactical', 'tactical_wide')
    version: str  # Version number for the video data collection in use (e.g. '0.1.0')
    name: str  # Vendor name of the video data
    fps: int  # Frames per second (i.e., frame rate) of video


class Event(TypedDict):
    collection_timing: (
        str  # Indicates if the event data was collected live or post match
    )


class Tracking(TypedDict):
    version: (
        str  # Version number for the tracking data collection in use (e.g. '0.1.0')
    )
    name: str  # Vendor name of the tracking data
    fps: int  # Frames per second (i.e., frame rate) of tracking
    collection_timing: (
        str  # Indicates if the tracking data was collected live or post match
    )


class Limb(TypedDict):
    version: str  # Version number for the limb data collection in use (e.g. '0.1.0')
    name: str  # Vendor name of the limb tracking data
    fps: int  # Frames per second (i.e., frame rate) of limb tracking
    collection_timing: (
        str  # Indicates if the limb data was collected live or post match
    )


class Ball(TypedDict):
    version: str  # Version number for the ball data collection in use
    name: str  # Vendor name of the ball data
    fps: int  # Frames per second (i.e., frame rate) of ball tracking
    collection_timing: (
        str  # Indicates if the ball data was collected live or post match
    )


class Meta1(TypedDict):
    version: str  # Version number for the meta data collection in use
    name: str  # Vendor name of the meta data


class Cdf(TypedDict):
    version: str  # Version number for the CDF in use


class Meta(TypedDict):
    video: Optional[Video]  # Video meta data information, null if not relevant
    event: NotRequired[
        Optional[Event]
    ]  # Event data meta information, null if not relevant
    tracking: Optional[Tracking]  # Tracking data meta information, null if not relevant
    limb: NotRequired[
        Optional[Limb]
    ]  # Limb tracking data meta information, null if not relevant
    ball: NotRequired[
        Optional[Ball]
    ]  # Ball tracking data meta information, null if not relevant. Only relevant when providing an independent ball file.
    meta: Optional[Meta1]  # Meta information
    cdf: Optional[Cdf]  # Common Data Format (CDF) meta information


class Player(TypedDict):
    id: str  # Unique player identifier
    team_id: str  # Unique team identifier denoting the team the player plays for
    jersey_number: int  # Jersey number for a player
    is_starter: bool  # Denotes whether a player started the game (true) or not (false)


class Team(TypedDict):
    id: str  # Unique identifier for the home team
    players: List[Player]


class Teams(TypedDict):
    home: Team
    away: Team


class CdfMetaDataSchema(TypedDict):
    competition: Competition
    season: Season
    match: Match
    teams: Teams
    stadium: Stadium
    meta: Meta
