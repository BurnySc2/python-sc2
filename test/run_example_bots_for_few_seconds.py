"""
This script makes sure to run all bots in the examples folder to check if they can launch.
"""
import os
import sys
from itertools import combinations

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from importlib import import_module
from typing import Type

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race, Result
from sc2.main import run_game
from sc2.player import Bot, Computer

# Time limit given in seconds of total in game time
game_time_limit_vs_computer = 30
game_time_limit_vs_computer_realtime = 5
game_time_limit_bot_vs_bot = 10
game_time_limit_bot_vs_bot_realtime = 5

bot_infos = [
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
for bot_info in bot_infos:
    for realtime in [True, False]:
        bot_race: Race = bot_info["race"]
        bot_path: str = bot_info["path"]
        bot_class_name: str = bot_info["bot_class_name"]
        module = import_module(bot_path)
        bot_class: Type[BotAI] = getattr(module, bot_class_name)

        result: Result = run_game(
            maps.get("Acropolis"),
            [Bot(bot_race, bot_class()), Computer(Race.Protoss, Difficulty.Easy)],
            realtime=realtime,
            game_time_limit=game_time_limit_vs_computer_realtime if realtime else game_time_limit_vs_computer,
        )
        assert result == Result.Tie, f"{result} in bot vs computer: {bot_class} in realtime={realtime}"

# Run bots against each other
for bot_info1, bot_info2 in combinations(bot_infos, 2):
    bot_race1: Race = bot_info1["race"]
    bot_path: str = bot_info1["path"]
    bot_class_name: str = bot_info1["bot_class_name"]
    module = import_module(bot_path)
    bot_class1: Type[BotAI] = getattr(module, bot_class_name)

    bot_race2: Race = bot_info2["race"]
    bot_path: str = bot_info2["path"]
    bot_class_name: str = bot_info2["bot_class_name"]
    module = import_module(bot_path)
    bot_class2: Type[BotAI] = getattr(module, bot_class_name)

    for realtime in [True, False]:
        result: Result = run_game(
            maps.get("Acropolis"),
            [
                Bot(bot_race1, bot_class1()),
                Bot(bot_race2, bot_class2()),
            ],
            realtime=realtime,
            game_time_limit=game_time_limit_bot_vs_bot_realtime if realtime else game_time_limit_bot_vs_bot,
        )
        assert result == [
            Result.Tie, Result.Tie
        ], f"{result} in bot vs bot: {bot_class1} vs {bot_class2} in realtime={realtime}"
