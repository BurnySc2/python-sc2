"""
This bot tests if battery overcharge crashes the bot.
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from loguru import logger

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.main import run_game
from sc2.player import Bot, Computer


class BatteryOverchargeBot(BotAI):
    async def on_start(self):
        """ Spawn requires structures. """
        await self.client.debug_create_unit(
            [
                [UnitTypeId.PYLON, 1, self.start_location.towards(self.game_info.map_center, 5), 1],
                [UnitTypeId.SHIELDBATTERY, 1,
                 self.start_location.towards(self.game_info.map_center, 5), 1],
                [UnitTypeId.CYBERNETICSCORE, 1,
                 self.start_location.towards(self.game_info.map_center, 5), 1],
            ]
        )

    async def on_step(self, iteration):
        if iteration > 10:
            # Cast battery overcharge
            nexi = self.structures(UnitTypeId.NEXUS)
            batteries = self.structures(UnitTypeId.SHIELDBATTERY)
            for nexus in nexi:
                for battery in batteries:
                    if nexus.energy >= 50:
                        nexus(AbilityId.BATTERYOVERCHARGE_BATTERYOVERCHARGE, battery)

        if iteration > 20:
            logger.warning(f"Success, bot did not crash. Exiting bot.")
            await self.client.leave()


def main():
    run_game(
        maps.get("AcropolisLE"),
        [Bot(Race.Protoss, BatteryOverchargeBot()),
         Computer(Race.Terran, Difficulty.Medium)],
        realtime=False,
        disable_fog=True,
    )


if __name__ == "__main__":
    main()
