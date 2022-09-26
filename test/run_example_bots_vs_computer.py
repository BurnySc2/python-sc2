"""
This script makes sure to run all bots in the examples folder to check if they can launch.
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import asyncio
from importlib import import_module
from typing import List, Type

from loguru import logger

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race, Result
from sc2.main import GameMatch, a_run_multiple_games_nokill
from sc2.player import Bot, Computer

# Time limit given in seconds of total in game time
game_time_limit_vs_computer = 120

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
    # # Other
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

matches: List[GameMatch] = []

# Run example bots
for bot_info in bot_infos:
    bot_race: Race = bot_info["race"]
    bot_path: str = bot_info["path"]
    bot_class_name: str = bot_info["bot_class_name"]
    module = import_module(bot_path)
    bot_class: Type[BotAI] = getattr(module, bot_class_name)

    limit_match_duration = game_time_limit_vs_computer
    if bot_class_name in {"SlowBot", "RampWallBot"}:
        limit_match_duration = 2

    matches.append(
        GameMatch(
            map_sc2=maps.get("Acropolis"),
            players=[Bot(bot_race, bot_class()), Computer(Race.Protoss, Difficulty.Easy)],
            realtime=False,
            game_time_limit=limit_match_duration,
        )
    )


async def main():
    results = await a_run_multiple_games_nokill(matches)

    # Verify results
    for result, game_match in zip(results, matches):
        # Zergrush bot sets variable to True when on_end was called
        if hasattr(game_match.players[0], "on_end_called"):
            assert getattr(game_match.players[0], "on_end_called", False) is True

        assert all(
            v == Result.Tie for k, v in result.items()
        ), f"result={result} in bot vs computer: {game_match.players[0]} in realtime={game_match.realtime}"
    logger.info("Checked all results")


if __name__ == '__main__':
    asyncio.run(main())
