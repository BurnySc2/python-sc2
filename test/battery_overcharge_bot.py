import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import sc2
from sc2.position import Point2, Point3
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.data import Result
from sc2.player import Bot, Computer
from sc2.unit import Unit
from sc2.units import Units
from loguru import logger

"""
This bot tests if battery overcharge crashes the bot.
"""


class BatteryOverchargeBot(sc2.BotAI):
    async def on_start(self):
        """ Spawn requires structures. """
        await self.client.debug_create_unit(
            [
                [UnitTypeId.PYLON, 1, self.start_location.towards(self.game_info.map_center, 5), 1],
                [UnitTypeId.SHIELDBATTERY, 1, self.start_location.towards(self.game_info.map_center, 5), 1],
                [UnitTypeId.CYBERNETICSCORE, 1, self.start_location.towards(self.game_info.map_center, 5), 1],
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
    sc2.run_game(
        sc2.maps.get("AcropolisLE"),
        [Bot(Race.Protoss, BatteryOverchargeBot()), Computer(Race.Terran, Difficulty.Medium)],
        realtime=False,
        disable_fog=True,
    )


if __name__ == "__main__":
    main()
