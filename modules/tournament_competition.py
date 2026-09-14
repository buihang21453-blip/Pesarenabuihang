"""Tournament competition composition root (V1.5.78).

The former 4k+ line tournament competition monolith is split by responsibility
under ``modules/tournament_competition_parts``. Public registration remains
``register_routes(context)`` so ``app.py`` and Flask endpoint names stay stable.
"""
from datetime import datetime, timezone, timedelta
import json
import random
import uuid

from teams_data import TEAMS

from modules.tournament_competition_parts.core import register_core
from modules.tournament_competition_parts.admin import register_admin
from modules.tournament_competition_parts.test_support import register_test_support
from modules.tournament_competition_parts.rooms import register_rooms
from modules.tournament_competition_parts.league import register_league
from modules.tournament_competition_parts.scheduling import register_scheduling
from modules.tournament_competition_parts.rewards import register_rewards

STAGE_LABELS = {
    "stage1": "GĐ1 · Phân hạng",
    "league": "League Phase",
    "knockout": "Knockout",
}
ROUND_ORDER = ["playoff", "r16", "qf", "sf", "final"]
STAGE1_ALLOWED_TIERS = {"S+", "S"}
TOURNAMENT_ROOM_PREFIX = "TOURNAMENT_ROOM|"

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
