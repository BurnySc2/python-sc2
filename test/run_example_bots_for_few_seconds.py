"""
This script makes sure to run all bots in the examples folder to check if they can launch.
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from importlib import import_module
from typing import Type

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race, Result
from sc2.main import run_game
from sc2.player import Bot, Computer

game_time_limit = 60  # 60 seconds in game time

bot_paths = [
    # Protoss
    {
        "race": Race.Protoss,
        "path": "examples.protoss.cannon_rush",
        "bot_class_name": "CannonRushBot"
    },
    {
        "race": Race.Protoss,
        "path": "examples.protoss.find_adept_shades",
        "bot_class_name": "FindAdeptShadesBot"
    },
    {
        "race": Race.Protoss,
        "path": "examples.protoss.threebase_voidray",
        "bot_class_name": "ThreebaseVoidrayBot"
    },
    {
        "race": Race.Protoss,
        "path": "examples.protoss.warpgate_push",
        "bot_class_name": "WarpGateBot"
    },
    # Terran
    {
        "race": Race.Terran,
        "path": "examples.terran.cyclone_push",
        "bot_class_name": "CyclonePush"
    },
    {
        "race": Race.Terran,
        "path": "examples.terran.mass_reaper",
        "bot_class_name": "MassReaperBot"
    },
    {
        "race": Race.Terran,
        "path": "examples.terran.onebase_battlecruiser",
        "bot_class_name": "BCRushBot"
    },
    {
        "race": Race.Terran,
        "path": "examples.terran.proxy_rax",
        "bot_class_name": "ProxyRaxBot"
    },
    {
        "race": Race.Terran,
        "path": "examples.terran.ramp_wall",
        "bot_class_name": "RampWallBot"
    },
    # Zerg
    {
        "race": Race.Zerg,
        "path": "examples.zerg.expand_everywhere",
        "bot_class_name": "ExpandEverywhere"
    },
    {
        "race": Race.Zerg,
        "path": "examples.zerg.hydralisk_push",
        "bot_class_name": "Hydralisk"
    },
    {
        "race": Race.Zerg,
        "path": "examples.zerg.onebase_broodlord",
        "bot_class_name": "BroodlordBot"
    },
    {
        "race": Race.Zerg,
        "path": "examples.zerg.zerg_rush",
        "bot_class_name": "ZergRushBot"
    },
    # Other
    {
        "race": Race.Protoss,
        "path": "examples.worker_stack_bot",
        "bot_class_name": "WorkerStackBot"
    },
    {
        "race": Race.Zerg,
        "path": "examples.worker_rush",
        "bot_class_name": "WorkerRushBot"
    },
    {
        "race": Race.Terran,
        "path": "examples.too_slow_bot",
        "bot_class_name": "SlowBot"
    },
    {
        "race": Race.Terran,
        "path": "examples.distributed_workers",
        "bot_class_name": "TerranBot"
    },
]

# Run example bots
for bot_info in bot_paths:
    bot_race: Race = bot_info["race"]
    bot_path: str = bot_info["path"]
    bot_class_name: str = bot_info["bot_class_name"]
    module = import_module(bot_path)
    bot_class: Type[BotAI] = getattr(module, bot_class_name)

    result: Result = run_game(
        maps.get("Acropolis"),
        [Bot(Race.Protoss, bot_class()), Computer(Race.Protoss, Difficulty.Easy)],
        realtime=False,
        game_time_limit=game_time_limit,
    )
    assert result == Result.Tie, f"{result}"
