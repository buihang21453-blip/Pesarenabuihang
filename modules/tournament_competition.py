"""Tournament competition composition root (V1.5.84).

The former 4k+ line tournament competition monolith is split by responsibility
under ``modules/tournament_competition_parts``. Public registration remains
``register_routes(context)`` so ``app.py`` and Flask endpoint names stay stable.
"""
from datetime import datetime, timezone, timedelta
import json
import random
import uuid

from teams_data import TEAMS

from modules.tournament_competition_parts import core as _core_part
from modules.tournament_competition_parts import admin as _admin_part
from modules.tournament_competition_parts import test_support as _test_support_part
from modules.tournament_competition_parts import rooms as _rooms_part
from modules.tournament_competition_parts import league as _league_part
from modules.tournament_competition_parts import scheduling as _scheduling_part
from modules.tournament_competition_parts import rewards as _rewards_part

register_core = _core_part.register_core
register_admin = _admin_part.register_admin
register_test_support = _test_support_part.register_test_support
register_rooms = _rooms_part.register_rooms
register_league = _league_part.register_league
register_scheduling = _scheduling_part.register_scheduling
register_rewards = _rewards_part.register_rewards

_COMPETITION_PARTS = (
    _core_part,
    _admin_part,
    _test_support_part,
    _rooms_part,
    _league_part,
    _scheduling_part,
    _rewards_part,
)

STAGE_LABELS = {
    "stage1": "GĐ1 · Phân hạng",
    "league": "League Phase",
    "knockout": "Knockout",
}
ROUND_ORDER = ["playoff", "r16", "qf", "sf", "final"]
STAGE1_ALLOWED_TIERS = {"S+", "S"}
TOURNAMENT_ROOM_PREFIX = "TOURNAMENT_ROOM|"
KNOCKOUT_UNLOCK_KEY = "knockout_match_unlocks_v1"

C1_CLUB_POTS = {
    1: ["Bayern", "Real Madrid", "Barcelona", "PSG", "Liverpool", "Man City", "Arsenal", "Inter"],
    2: ["Atlético Madrid", "Man United", "Aston Villa", "Napoli", "Roma", "Fenerbahçe", "Galatasaray", "Dortmund"],
    3: ["PSV", "Villarreal", "Real Betis", "Lille", "Lens", "Como", "Porto", "RB Leipzig"],
}
C1_CLUB_POOL = [name for pot in C1_CLUB_POTS.values() for name in pot]
C1_CLUB_POT_BY_NAME = {name: pot for pot, names in C1_CLUB_POTS.items() for name in names}


def register_routes(context):
    """Register all C1 competition routes in deterministic dependency order."""
    shared = dict(context)
    shared.update({
        "datetime": datetime,
        "timezone": timezone,
        "timedelta": timedelta,
        "json": json,
        "random": random,
        "uuid": uuid,
        "TEAMS": TEAMS,
        "STAGE_LABELS": STAGE_LABELS,
        "ROUND_ORDER": ROUND_ORDER,
        "STAGE1_ALLOWED_TIERS": STAGE1_ALLOWED_TIERS,
        "TOURNAMENT_ROOM_PREFIX": TOURNAMENT_ROOM_PREFIX,
        "KNOCKOUT_UNLOCK_KEY": KNOCKOUT_UNLOCK_KEY,
        "C1_CLUB_POTS": C1_CLUB_POTS,
        "C1_CLUB_POOL": C1_CLUB_POOL,
        "C1_CLUB_POT_BY_NAME": C1_CLUB_POT_BY_NAME,
    })

    # Core helpers/context processors first; later partitions consume these helpers.
    for registrar in (
        register_core,
        register_admin,
        register_test_support,
        register_rooms,
        register_league,
        register_scheduling,
        register_rewards,
    ):
        exported = registrar(shared) or {}
        shared.update(exported)

    # V1.5.84: the legacy monolith allowed functions in any section to resolve
    # helpers/constants declared later in the same module. After V1.5.84 split,
    # each part had an isolated module namespace, so forward cross-part references
    # could raise NameError at request time (notably /admin tournament context).
    # Synchronize the completed shared namespace back into every partition.
    for part in _COMPETITION_PARTS:
        part.__dict__.update(shared)
