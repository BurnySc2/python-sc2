from loguru import logger

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2.position import Point2

MY_PLAYER_ID = 1
OPPONENT_PLAYER_ID = 2


class FightBot(BotAI):

    def __init__(self):
        super().__init__()
        self.enemy_location: Point2 = None
        self.fight_started = False

    async def on_start(self):
        # Retrieve control by enabling enemy control and showing whole map
        await self.client.debug_show_map()
        await self.client.debug_control_enemy()

    async def on_step(self, iteration):
        # Wait till control retrieved, destroy all starting units, recreate the world
        if iteration > 0 and self.enemy_units and not self.enemy_location:
            await self.reset_arena()

        if (self.units or self.structures) and (self.enemy_units or self.enemy_structures):
            self.enemy_location = (self.enemy_units + self.enemy_structures).center
            self.fight_started = True

        await self.manage_enemy_units()
        await self.manage_own_units()

        # In case of no units left - do not wait for game to finish
        if self.fight_started and (not self.units or not self.enemy_units):
            logger.info("LOSE" if not self.units else "WIN")
            await self.client.quit()  # or reset level
            return

    async def reset_arena(self):
        await self.client.debug_kill_unit(self.all_units)

        await self.client.debug_create_unit(
            [
                [UnitTypeId.SUPPLYDEPOT, 1, self.enemy_location, OPPONENT_PLAYER_ID],
                [UnitTypeId.MARINE, 4,
                 self.enemy_location.towards(self.start_location, 8), OPPONENT_PLAYER_ID]
            ]
        )

        await self.client.debug_create_unit(
            [
                [UnitTypeId.SUPPLYDEPOT, 1, self.start_location, MY_PLAYER_ID],
                [UnitTypeId.MARINE, 4,
                 self.start_location.towards(self.enemy_location, 8), MY_PLAYER_ID]
            ]
        )

    async def manage_enemy_units(self):
        for unit in self.enemy_units:
            unit.attack(self.start_location)

    async def manage_own_units(self):
        for unit in self.units(UnitTypeId.MARINE):
            unit.attack(self.enemy_location)
            # TODO: implement your fight logic here
            # if unit.weapon_cooldown != 0:
            #     unit.move(u.position.towards(self.start_location))
            # else:
            #     unit.attack(self.enemy_location)
            # pass


def main():
    run_game(
        maps.get("Flat64"),
        # NOTE: you can have two bots fighting with each other here
        [Bot(Race.Terran, FightBot()), Computer(Race.Terran, Difficulty.Medium)],
        realtime=True
    )


if __name__ == "__main__":
    main()
