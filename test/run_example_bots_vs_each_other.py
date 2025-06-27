# pyre-ignore-all-errors[16]
"""
This script makes sure to run all bots in the examples folder to check if they can launch against each other.
"""

from __future__ import annotations

import asyncio
from importlib import import_module
from itertools import combinations

from loguru import logger

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Race, Result
from sc2.main import GameMatch, a_run_multiple_games_nokill
from sc2.player import Bot

# Time limit given in seconds of total in game time
game_time_limit_bot_vs_bot = 10
game_time_limit_bot_vs_bot_realtime = 2

bot_infos = [
    # Protoss
    {
        "race": Race.Protoss,
        "path": "examples.protoss.cannon_rush",
        "bot_class_name": "CannonRushBot",
    },
    {
        "race": Race.Protoss,
        "path": "examples.protoss.find_adept_shades",
        "bot_class_name": "FindAdeptShadesBot",
    },
    {
        "race": Race.Protoss,
        "path": "examples.protoss.threebase_voidray",
        "bot_class_name": "ThreebaseVoidrayBot",
    },
    {
        "race": Race.Protoss,
        "path": "examples.protoss.warpgate_push",
        "bot_class_name": "WarpGateBot",
    },
    # Terran
    {
        "race": Race.Terran,
        "path": "examples.terran.cyclone_push",
        "bot_class_name": "CyclonePush",
    },
    {
        "race": Race.Terran,
        "path": "examples.terran.mass_reaper",
        "bot_class_name": "MassReaperBot",
    },
    {
        "race": Race.Terran,
        "path": "examples.terran.onebase_battlecruiser",
        "bot_class_name": "BCRushBot",
    },
    {
        "race": Race.Terran,
        "path": "examples.terran.proxy_rax",
        "bot_class_name": "ProxyRaxBot",
    },
    {
        "race": Race.Terran,
        "path": "examples.terran.ramp_wall",
        "bot_class_name": "RampWallBot",
    },
    # Zerg
    {
        "race": Race.Zerg,
        "path": "examples.zerg.expand_everywhere",
        "bot_class_name": "ExpandEverywhere",
    },
    {
        "race": Race.Zerg,
        "path": "examples.zerg.hydralisk_push",
        "bot_class_name": "Hydralisk",
    },
    {
        "race": Race.Zerg,
        "path": "examples.zerg.onebase_broodlord",
        "bot_class_name": "BroodlordBot",
    },
    {
        "race": Race.Zerg,
        "path": "examples.zerg.zerg_rush",
        "bot_class_name": "ZergRushBot",
    },
]

matches: list[GameMatch] = []

# Run bots against each other
for bot_info1, bot_info2 in combinations(bot_infos, 2):
    # pyre-ignore[11]
    bot_race1: Race = bot_info1["race"]
    bot_path: str = bot_info1["path"]
    bot_class_name: str = bot_info1["bot_class_name"]
    module = import_module(bot_path)
    bot_class1: type[BotAI] = getattr(module, bot_class_name)

    bot_race2: Race = bot_info2["race"]
    bot_path: str = bot_info2["path"]
    bot_class_name: str = bot_info2["bot_class_name"]
    module = import_module(bot_path)
    bot_class2: type[BotAI] = getattr(module, bot_class_name)

    for realtime in [True, False]:
        matches.append(
            GameMatch(
                map_sc2=maps.get("Acropolis"),
                players=[
                    Bot(bot_race1, bot_class1()),
                    Bot(bot_race2, bot_class2()),
                ],
                realtime=False,
                game_time_limit=game_time_limit_bot_vs_bot_realtime if realtime else game_time_limit_bot_vs_bot,
            )
        )


async def main():
    results = await a_run_multiple_games_nokill(matches)

    # Verify results
    for result, game_match in zip(results, matches):
        # Zergrush bot sets variable to True when on_end was called
        if hasattr(game_match.players[0], "on_end_called"):
            assert getattr(game_match.players[0], "on_end_called", False) is True

        assert all(v == Result.Tie for k, v in result.items()), (
            f"result={result} in bot vs bot: {game_match.players[0]} vs {game_match.players[1]} in realtime={game_match.realtime}"
        )
    logger.info("Checked all results")


if __name__ == "__main__":
    asyncio.run(main())
