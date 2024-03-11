from datetime import datetime
from typing import Any, Literal, Optional, TypedDict

import pydantic


class PlayerNameType(TypedDict):
    id: int
    name: str
    steam_id_64: str
    created: datetime
    last_seen: datetime


class PlayerSessionType(TypedDict):
    id: int
    steam_id_64: str
    start: Optional[datetime]
    end: Optional[datetime]
    created: datetime


class PlayerActionType(TypedDict):
    action_type: str
    reason: Optional[str]
    by: Optional[str]
    time: datetime


class PenaltyCountType(TypedDict):
    KICK: int
    PUNISH: int
    TEMPBAN: int
    PERMABAN: int


class BlackListType(TypedDict):
    steam_id_64: str
    is_blacklisted: bool
    reason: Optional[str]
    by: Optional[str]


class PlayerFlagType(TypedDict):
    id: int
    flag: str
    comment: Optional[str]
    modified: datetime


class WatchListType(TypedDict):
    id: int
    modified: datetime
    steam_id_64: str
    is_watched: bool
    reason: str
    by: str
    count: int


class SteamPlayerSummaryType(TypedDict):
    """Result of steam API ISteamUser.GetPlayerSummaries"""

    avatar: str
    avatarfull: str
    avatarhash: str
    avatarmedium: str
    # 1 - not visible 3 - visibile
    communityvisibilitystate: Literal[1] | Literal[3]
    lastlogoff: int
    loccityid: int
    loccountrycode: str
    locstatecode: str
    personaname: str
    personastate: int
    personastateflags: int
    primaryclanid: str
    profilestate: int
    profileurl: str
    realname: str
    steamid: str
    timecreated: int


class SteamBansType(TypedDict):
    """Result of steam API ISteamUser.GetPlayerBans"""

    SteamId: str
    CommunityBanned: bool
    VACBanned: bool
    NumberOfVACBans: int
    DaysSinceLastBan: int
    NumberOfGameBans: int
    EconomyBan: str


class SteamInfoType(TypedDict):
    """Dictionary version of SteamInfo model"""

    id: int
    created: datetime
    updated: datetime
    profile: SteamPlayerSummaryType | None
    country: str | None
    bans: SteamBansType | None
    has_bans: bool


class PlayerVIPType(TypedDict):
    server_number: int
    expiration: datetime
    vip_name: str


class PlayerProfileType(TypedDict):
    id: int
    steam_id_64: str
    created: datetime
    names: list[PlayerNameType]
    sessions: list[PlayerSessionType]
    sessions_count: int
    total_playtime_seconds: int
    current_playtime_seconds: int
    received_actions: list[PlayerActionType]
    penalty_count: PenaltyCountType
    blacklist: Optional[BlackListType]
    flags: list[PlayerFlagType]
    watchlist: Optional[WatchListType]
    steaminfo: Optional[SteamInfoType]
    vips: list[PlayerVIPType]


class RconAPIResponse(TypedDict):
    result: Any
    command: str
    arguments: dict[str, Any]
    failed: bool
    error: str
    forwards_results: bool


class VipPlayer(pydantic.BaseModel):
    name: str
    steam_id_64: str
    expiration_date: datetime | None
