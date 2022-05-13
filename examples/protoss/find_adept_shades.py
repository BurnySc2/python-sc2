import math

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2.position import Point2


# pylint: disable=W0231
class FindAdeptShadesBot(BotAI):

    def __init__(self):
        self.shaded = False
        self.shades_mapping = {}

    async def on_start(self):
        self.client.game_step = 2
        await self.client.debug_create_unit(
            [[UnitTypeId.ADEPT, 10, self.townhalls[0].position.towards(self.game_info.map_center, 5), 1]]
        )

    async def on_step(self, iteration: int):
        adepts = self.units(UnitTypeId.ADEPT)
        if adepts and not self.shaded:
            # Wait for adepts to spawn and then cast ability
            for adept in adepts:
                adept(AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT, self.game_info.map_center)
            self.shaded = True
        elif self.shades_mapping:
            # Debug log and draw a line between the two units
            for adept_tag, shade_tag in self.shades_mapping.items():
                adept = self.units.find_by_tag(adept_tag)
                shade = self.units.find_by_tag(shade_tag)
                if shade:
                    # logger.info(f"Remaining shade time: {shade.buff_duration_remain} / {shade.buff_duration_max}")
                    pass
                if adept and shade:
                    self.client.debug_line_out(adept, shade, (0, 255, 0))
            # logger.info(self.shades_mapping)
        elif self.shaded:
            # Find shades
            shades = self.units(UnitTypeId.ADEPTPHASESHIFT)
            for shade in shades:
                remaining_adepts = adepts.tags_not_in(self.shades_mapping)
                # Figure out where the shade should have been "self.client.game_step"-frames ago
                forward_position = Point2(
                    (shade.position.x + math.cos(shade.facing), shade.position.y + math.sin(shade.facing))
                )
                previous_shade_location = shade.position.towards(
                    forward_position, -(self.client.game_step / 16) * shade.movement_speed
                )  # See docstring of movement_speed attribute
                closest_adept = remaining_adepts.closest_to(previous_shade_location)
                self.shades_mapping[closest_adept.tag] = shade.tag


def main():
    run_game(
        maps.get("(2)CatalystLE"),
        [Bot(Race.Protoss, FindAdeptShadesBot()),
         Computer(Race.Protoss, Difficulty.Medium)],
        realtime=False,
    )


if __name__ == "__main__":
    main()
