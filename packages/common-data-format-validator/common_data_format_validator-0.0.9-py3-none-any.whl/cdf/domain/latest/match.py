# Auto-generated from JSON Schema v0.2.1
# Do not edit manually - run generate_latest_domain.py


from __future__ import annotations

from typing import List, Literal, Optional, TypedDict

from typing_extensions import NotRequired


class Status(TypedDict):
    is_neutral: bool  # Denotes whether the game was hosted in a neutral venue (true) or not (false)
    has_extratime: (
        bool  # Denotes whether the game went to extra time (true) or not (false)
    )
    has_shootout: (
        bool  # Denotes whether the game had a penalty shootout (true) or not (false)
    )


class Final(TypedDict):
    home: int  # Final result for home team
    away: int  # Final result for away team


class FirstHalf(TypedDict):
    home: int  # First half result for home team
    away: int  # First half result for away team


class SecondHalf(TypedDict):
    home: int  # Second half result for home team
    away: int  # Second half result for away team


class FirstHalfExtratime(TypedDict):
    home: int  # First half extratime result for home team
    away: int  # First half extratime result for away team


class SecondHalfExtratime(TypedDict):
    home: int  # Second half extratime result for home team
    away: int  # Second half extratime result for away team


class Shootout(TypedDict):
    home: int  # Shootout result for home team
    away: int  # Shootout result for away team


class Result(TypedDict):
    final: Final
    final_winning_team_id: str  # Unique identifier of the winning team
    first_half: FirstHalf
    second_half: SecondHalf
    first_half_extratime: NotRequired[
        FirstHalfExtratime
    ]  # Required if has_extratime is true
    second_half_extratime: NotRequired[
        SecondHalfExtratime
    ]  # Required if has_extratime is true
    shootout: NotRequired[Shootout]  # Required if has_shootout is true


class Match(TypedDict):
    id: str  # Unique match identifier
    status: Status
    result: Result


class Referee(TypedDict):
    id: str  # Unique referee identifier
    official_type: NotRequired[
        str
    ]  # The type of referee (e.g. video_assistant_referee, main_referee, assistant_referee or fourth_official
    first_name: NotRequired[str]  # First name
    last_name: NotRequired[str]  # Last name
    short_name: NotRequired[str]  # Short name


class Score(TypedDict):
    home: int  # Home team score after this goal
    away: int  # Away team score after this goal


class Goal(TypedDict):
    time: str  # Time a player scored
    period: Literal[
        "first_half",
        "second_half",
        "first_half_extratime",
        "second_half_extratime",
        "shootout",
    ]  # Period of the game when the goal was scored
    team_id: str  # Identifier of the team who scored
    player_id: str  # Identifier of the player who scored
    assist_id: NotRequired[Optional[str]]  # Identifier of the player who assisted
    is_own_goal: bool  # Denotes whether it was an own goal (true) or not (false)
    is_penalty: bool  # Denotes whether it was a penalty (true) or not (false)
    score: Score


class Substitution(TypedDict):
    team_id: str  # Identifier of the team who scored
    in_time: str  # Time a player is substituted in
    period: Literal[
        "first_half", "second_half", "first_half_extratime", "second_half_extratime"
    ]  # Period of the game when the substitution occurred
    in_player_id: str  # Identifier of the player that is substituted in
    out_time: str  # Time a player is substituted out
    out_player_id: str  # Identifier of the player that is substituted out


class Card(TypedDict):
    team_id: str  # Identifier of the team who scored
    time: str  # Time a player received a card
    period: Literal[
        "first_half", "second_half", "first_half_extratime", "second_half_extratime"
    ]  # Period of the game when the card was shown
    player_id: str  # Identifier of the player who received a card
    type: Literal[
        "yellow_card", "red_card", "second_yellow_card"
    ]  # Type of card which can be yellow card, red card or second yellow card


class Events(TypedDict):
    goals: Optional[List[Goal]]
    substitutions: Optional[List[Substitution]]
    cards: Optional[List[Card]]


class Meta(TypedDict):
    vendor: str  # Match sheet data vendor name


class Player(TypedDict):
    id: str  # Unique player identifier
    first_name: str  # First name
    last_name: str  # Last name
    short_name: NotRequired[str]  # Short name
    team_id: str  # Unique team identifier denoting the team the player plays for
    jersey_number: int  # Jersey number for a player
    is_starter: bool  # Denotes whether a player started the game (true) or not (false)
    has_played: bool  # Denotes whether a player played in game (true) or not (false)
    maiden_name: NotRequired[str]  # Maiden name
    position_group: NotRequired[
        Literal["GK", "DF", "MF", "FW", "SUB"]
    ]  # Position group acronym given according to the CDF-compatible groups
    position: NotRequired[
        Literal[
            "GK",
            "LB",
            "LCB",
            "CB",
            "RCB",
            "RB",
            "LDM",
            "CDM",
            "RDM",
            "LM",
            "LCM",
            "CM",
            "RCM",
            "RM",
            "LAM",
            "CAM",
            "RAM",
            "LW",
            "LCF",
            "CF",
            "RCF",
            "RW",
            "SUB",
        ]
    ]  # Position label acronym per player given according to the CDF-compatible labels
    is_captain: NotRequired[
        bool
    ]  # Whether the player is a captain (true) or not (false)
    date_of_birth: NotRequired[str]  # A player's date of birth in YYYY-MM-DD format
    height: NotRequired[int]  # Height of a player in cm
    foot: NotRequired[
        Literal["left", "right", "both"]
    ]  # A player's dominant foot, which can take the values left, right or both
    alternative_id: NotRequired[str]  # Additional identifier(s) of the player


class Coach(TypedDict):
    id: str  # Unique identifier for a coach
    first_name: str  # First name
    last_name: str  # Last name
    short_name: NotRequired[str]  # Short name


class Team(TypedDict):
    id: str  # Unique identifier for the team
    short_name: NotRequired[str]  # Short name of the team
    formation: NotRequired[str]  # Formation label of the team (e.g. '4-4-2')
    players: List[Player]
    coaches: NotRequired[List[Coach]]


class Teams(TypedDict):
    home: Team
    away: Team


class OfficialMatchData(TypedDict):
    match: Match
    teams: Teams
    referees: List[Referee]
    events: Events
    meta: Meta
