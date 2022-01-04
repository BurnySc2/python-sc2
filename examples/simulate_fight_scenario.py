from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Race, Difficulty
from sc2.ids.unit_typeid import UnitTypeId
from sc2.main import run_game
from sc2.player import Bot, Computer
from loguru import logger

ME = 1
PC = 2


class FightBot(BotAI):
    def __init__(self):
        super().__init__()
        self.enemy_location = None
        self.fight_started = False

    async def on_step(self, iteration):
        # retrieve control by enabling enemy control and showing whole map
        if iteration == 0:
            await self._client.debug_show_map()
            await self._client.debug_control_enemy()

        # wait till control retrieved, destroy all starting units, recreate the world
        if iteration > 0 and self.enemy_units and not self.enemy_location:
            self.enemy_location = self.enemy_structures(UnitTypeId.COMMANDCENTER).first.position.closest(self.enemy_start_locations)
            await self._client.debug_kill_unit([u.tag for u in self.units + self.structures + self.enemy_units + self.enemy_structures])
            await self._client.debug_create_unit([
                [UnitTypeId.SUPPLYDEPOT, 1, self.enemy_location, PC],
                [UnitTypeId.MARINE, 4, self.enemy_location.towards(self.start_location, 8), PC]
            ])
            await self._client.debug_create_unit([
                [UnitTypeId.SUPPLYDEPOT, 1, self.start_location, ME],
                [UnitTypeId.MARINE, 4, self.start_location.towards(self.enemy_location, 8), ME]
            ])

        # wait till workers will be destroyed and start the fight
        if not self.fight_started and self.enemy_location and not self.enemy_units(UnitTypeId.SCV) and not self.units(UnitTypeId.SCV):
            for u in self.enemy_units:
                u.attack(self.start_location)
            for u in self.units:
                u.attack(self.enemy_location)
            self.fight_started = True

        # in case of no units left - do not wait for game to finish
        if self.fight_started and (not self.units or not self.enemy_units):
            logger.info("LOSE" if not self.units else "WIN")
            await self._client.quit()  # or reset level

        for u in self.units(UnitTypeId.MARINE):
            u.attack(self.enemy_structures.first.position)
            # TODO: implement your fight logic here
            # if u.weapon_cooldown:
            #     u.move(u.position.towards(self.structures.first.position))
            # else:
            #     u.attack(self.enemy_structures.first.position)
            # pass


def main():
    run_game(
        maps.get("Flat64"),
        # NOTE: you can have to bots fighting with each other here
        [Bot(Race.Terran, FightBot()), Computer(Race.Terran, Difficulty.Medium)],
        realtime=True
    )


if __name__ == "__main__":
    main()
