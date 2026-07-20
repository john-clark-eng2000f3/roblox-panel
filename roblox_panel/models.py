from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class Place:
    place_id: int
    name: str
    universe_id: int
    server_fill_rate: Optional[float] = None


@dataclass
class ServerInstance:
    server_id: str
    place_id: int
    player_count: int
    max_players: int
    fps: float
    ping_ms: float
    uptime_seconds: int
    players: List[str] = field(default_factory=list)


@dataclass
class LogEntry:
    timestamp: datetime
    severity: str
    message: str
    server_id: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricSnapshot:
    timestamp: datetime
    universe_id: int
    player_count: int
    server_count: int
    avg_fps: float
    avg_ping: float


@dataclass
class Universe:
    """Top-level Roblox experience container."""
    universe_id: int
    name: str
    creator_name: str
    root_place_id: int
    active_players: int = 0
    favorite_count: int = 0
    places: List[Place] = field(default_factory=list)
