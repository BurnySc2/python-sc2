import sc2
from sc2 import Race
from sc2.player import Bot

from sc2.units import Units
from sc2.unit import Unit
from sc2.position import Point2, Point3

from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.buff_id import BuffId
from sc2.ids.ability_id import AbilityId

from typing import List, Dict, Set, Tuple, Any, Optional, Union  # mypy type checking

"""
To play an arcade map, you need to download the map first.

Open the StarCraft2 Map Editor through the Battle.net launcher, in the top left go to
File -> Open -> (Tab) Blizzard -> Log in -> with "Source: Map/Mod Name" search for your desired map, in this example "Marine Split Challenge-LOTV" map created by printf
Hit "Ok" and confirm the download. Now that the map is opened, go to "File -> Save as" to store it on your hard drive.
Now load the arcade map by entering your map name below in
sc2.maps.get("YOURMAPNAME") without the .SC2Map extension


Map info:
You start with 30 marines, level N has 15+N speed banelings on creep

Type in game "sling" to activate zergling+baneling combo
Type in game "stim" to activate stimpack


Improvements that could be made:
- Make marines constantly run if they have a ling/bane very close to them
- Split marines before engaging
"""


class MarineSplitChallenge(sc2.BotAI):
    async def on_step(self, iteration):
        # do marine micro vs zerglings
        for unit in self.units(UnitTypeId.MARINE):

            if self.enemy_units:

                # attack (or move towards) zerglings / banelings
                if unit.weapon_cooldown <= self._client.game_step / 2:
                    enemies_in_range = self.enemy_units.filter(lambda u: unit.target_in_range(u))

                    # attack lowest hp enemy if any enemy is in range
                    if enemies_in_range:
                        # Use stimpack
                        if (
                            self.already_pending_upgrade(UpgradeId.STIMPACK) == 1
                            and not unit.has_buff(BuffId.STIMPACK)
                            and unit.health > 10
                        ):
                            self.do(unit(AbilityId.EFFECT_STIM))

                        # attack baneling first
                        filtered_enemies_in_range = enemies_in_range.of_type(UnitTypeId.BANELING)

                        if not filtered_enemies_in_range:
                            filtered_enemies_in_range = enemies_in_range.of_type(UnitTypeId.ZERGLING)
                        # attack lowest hp unit
                        lowest_hp_enemy_in_range = min(filtered_enemies_in_range, key=lambda u: u.health)
                        actions.append(unit.attack(lowest_hp_enemy_in_range))

                    # no enemy is in attack-range, so give attack command to closest instead
                    else:
                        closest_enemy = self.enemy_units.closest_to(unit)
                        self.do(unit.attack(closest_enemy))

                # move away from zergling / banelings
                else:
                    stutter_step_positions = self.position_around_unit(unit, distance=4)

                    # filter in pathing grid
                    stutter_step_positions = {p for p in stutter_step_positions if self.in_pathing_grid(p)}

                    # find position furthest away from enemies and closest to unit
                    enemies_in_range = self.known_enemy_units.filter(lambda u: unit.target_in_range(u, -0.5))

                    if stutter_step_positions and enemies_in_range:
                        retreat_position = max(
                            stutter_step_positions,
                            key=lambda x: x.distance_to(enemies_in_range.center) - x.distance_to(unit),
                        )
                        self.do(unit.move(retreat_position))

                    else:
                        print("No retreat positions detected for unit {} at {}.".format(unit, unit.position.rounded))

    async def on_start(self):
        await self.chat_send("Edit this message for automatic chat commands.")
        self._client.game_step = 4  # do actions every X frames instead of every 8th

    def position_around_unit(
        self,
        pos: Union[Unit, Point2, Point3],
        distance: int = 1,
        step_size: int = 1,
        exclude_out_of_bounds: bool = True,
    ):
        pos = pos.position.to2.rounded
        positions = {
            pos.offset(Point2((x, y)))
            for x in range(-distance, distance + 1, step_size)
            for y in range(-distance, distance + 1, step_size)
            if (x, y) != (0, 0)
        }
        # filter positions outside map size
        if exclude_out_of_bounds:
            positions = {
                p
                for p in positions
                if 0 <= p[0] < self._game_info.pathing_grid.width and 0 <= p[1] < self._game_info.pathing_grid.height
            }
        return positions


def main():
    sc2.run_game(
        sc2.maps.get("Marine Split Challenge"),
        [Bot(Race.Terran, MarineSplitChallenge())],
        realtime=False,
        save_replay_as="Example.SC2Replay",
    )


if __name__ == "__main__":
    main()
