import random
from typing import FrozenSet, Set

import numpy as np
from loguru import logger

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.units import Units


class RampWallBot(BotAI):

    # pylint: disable=W0231
    def __init__(self):
        self.unit_command_uses_self_do = False

    # pylint: disable=R0912
    async def on_step(self, iteration):
        ccs: Units = self.townhalls(UnitTypeId.COMMANDCENTER)
        if not ccs:
            return

        cc: Unit = ccs.first

        await self.distribute_workers()

        if self.can_afford(UnitTypeId.SCV) and self.workers.amount < 16 and cc.is_idle:
            cc.train(UnitTypeId.SCV)

        # Raise depos when enemies are nearby
        for depo in self.structures(UnitTypeId.SUPPLYDEPOT).ready:
            for unit in self.enemy_units:
                if unit.distance_to(depo) < 15:
                    break
            else:
                depo(AbilityId.MORPH_SUPPLYDEPOT_LOWER)

        # Lower depos when no enemies are nearby
        for depo in self.structures(UnitTypeId.SUPPLYDEPOTLOWERED).ready:
            for unit in self.enemy_units:
                if unit.distance_to(depo) < 10:
                    depo(AbilityId.MORPH_SUPPLYDEPOT_RAISE)
                    break

        # Draw ramp points
        self.draw_ramp_points()

        # Draw all detected expansions on the map
        self.draw_expansions()

        # # Draw pathing grid
        self.draw_pathing_grid()

        # Draw placement  grid
        self.draw_placement_grid()

        # Draw vision blockers
        self.draw_vision_blockers()

        # Draw visibility pixelmap for debugging purposes
        self.draw_visibility_pixelmap()

        # Draw some example boxes around units, lines towards command center, text on the screen and barracks
        self.draw_example()

        # Draw if two selected units are facing each other - green if this guy is facing the other, red if he is not
        self.draw_facing_units()

        depot_placement_positions: FrozenSet[Point2] = self.main_base_ramp.corner_depots
        # Uncomment the following if you want to build 3 supply depots in the wall instead of a barracks in the middle + 2 depots in the corner
        # depot_placement_positions = self.main_base_ramp.corner_depots | {self.main_base_ramp.depot_in_middle}

        barracks_placement_position: Point2 = self.main_base_ramp.barracks_correct_placement
        # If you prefer to have the barracks in the middle without room for addons, use the following instead
        # barracks_placement_position = self.main_base_ramp.barracks_in_middle

        depots: Units = self.structures.of_type({UnitTypeId.SUPPLYDEPOT, UnitTypeId.SUPPLYDEPOTLOWERED})

        # Filter locations close to finished supply depots
        if depots:
            depot_placement_positions: Set[Point2] = {
                d
                for d in depot_placement_positions if depots.closest_distance_to(d) > 1
            }

        # Build depots
        if self.can_afford(UnitTypeId.SUPPLYDEPOT) and self.already_pending(UnitTypeId.SUPPLYDEPOT) == 0:
            if len(depot_placement_positions) == 0:
                return
            # Choose any depot location
            target_depot_location: Point2 = depot_placement_positions.pop()
            workers: Units = self.workers.gathering
            if workers:  # if workers were found
                worker: Unit = workers.random
                worker.build(UnitTypeId.SUPPLYDEPOT, target_depot_location)

        # Build barracks
        if depots.ready and self.can_afford(UnitTypeId.BARRACKS) and self.already_pending(UnitTypeId.BARRACKS) == 0:
            if self.structures(UnitTypeId.BARRACKS).amount + self.already_pending(UnitTypeId.BARRACKS) > 0:
                return
            workers = self.workers.gathering
            if workers and barracks_placement_position:  # if workers were found
                worker: Unit = workers.random
                worker.build(UnitTypeId.BARRACKS, barracks_placement_position)

    async def on_building_construction_started(self, unit: Unit):
        logger.info(f"Construction of building {unit} started at {unit.position}.")

    async def on_building_construction_complete(self, unit: Unit):
        logger.info(f"Construction of building {unit} completed at {unit.position}.")

    def draw_ramp_points(self):
        for ramp in self.game_info.map_ramps:
            for p in ramp.points:
                h2 = self.get_terrain_z_height(p)
                pos = Point3((p.x, p.y, h2))
                color = Point3((255, 0, 0))
                if p in ramp.upper:
                    color = Point3((0, 255, 0))
                if p in ramp.upper2_for_ramp_wall:
                    color = Point3((0, 255, 255))
                if p in ramp.lower:
                    color = Point3((0, 0, 255))
                self.client.debug_box2_out(pos + Point2((0.5, 0.5)), half_vertex_length=0.25, color=color)
                # Identical to above:
                # p0 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z + 0.25))
                # p1 = Point3((pos.x + 0.75, pos.y + 0.75, pos.z - 0.25))
                # logger.info(f"Drawing {p0} to {p1}")
                # self.client.debug_box_out(p0, p1, color=color)

    def draw_expansions(self):
        green = Point3((0, 255, 0))
        for expansion_pos in self.expansion_locations_list:
            height = self.get_terrain_z_height(expansion_pos)
            expansion_pos3 = Point3((*expansion_pos, height))
            self.client.debug_box2_out(expansion_pos3, half_vertex_length=2.5, color=green)

    def draw_pathing_grid(self):
        map_area = self.game_info.playable_area
        for (b, a), value in np.ndenumerate(self.game_info.pathing_grid.data_numpy):
            if value == 0:
                continue
            # Skip values outside of playable map area
            if not map_area.x <= a < map_area.x + map_area.width:
                continue
            if not map_area.y <= b < map_area.y + map_area.height:
                continue
            p = Point2((a, b))
            h2 = self.get_terrain_z_height(p)
            pos = Point3((p.x, p.y, h2))
            p0 = Point3((pos.x - 0.25, pos.y - 0.25, pos.z + 0.25)) + Point2((0.5, 0.5))
            p1 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z - 0.25)) + Point2((0.5, 0.5))
            # logger.info(f"Drawing {p0} to {p1}")
            color = Point3((0, 255, 0))
            self.client.debug_box_out(p0, p1, color=color)

    def draw_placement_grid(self):
        map_area = self.game_info.playable_area
        for (b, a), value in np.ndenumerate(self.game_info.placement_grid.data_numpy):
            if value == 0:
                continue
            # Skip values outside of playable map area
            if not map_area.x <= a < map_area.x + map_area.width:
                continue
            if not map_area.y <= b < map_area.y + map_area.height:
                continue
            p = Point2((a, b))
            h2 = self.get_terrain_z_height(p)
            pos = Point3((p.x, p.y, h2))
            p0 = Point3((pos.x - 0.25, pos.y - 0.25, pos.z + 0.25)) + Point2((0.5, 0.5))
            p1 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z - 0.25)) + Point2((0.5, 0.5))
            # logger.info(f"Drawing {p0} to {p1}")
            color = Point3((0, 255, 0))
            self.client.debug_box_out(p0, p1, color=color)

    def draw_vision_blockers(self):
        for p in self.game_info.vision_blockers:
            h2 = self.get_terrain_z_height(p)
            pos = Point3((p.x, p.y, h2))
            p0 = Point3((pos.x - 0.25, pos.y - 0.25, pos.z + 0.25)) + Point2((0.5, 0.5))
            p1 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z - 0.25)) + Point2((0.5, 0.5))
            # logger.info(f"Drawing {p0} to {p1}")
            color = Point3((255, 0, 0))
            self.client.debug_box_out(p0, p1, color=color)

    def draw_visibility_pixelmap(self):
        for (y, x), value in np.ndenumerate(self.state.visibility.data_numpy):
            p = Point2((x, y))
            h2 = self.get_terrain_z_height(p)
            pos = Point3((p.x, p.y, h2))
            p0 = Point3((pos.x - 0.25, pos.y - 0.25, pos.z + 0.25)) + Point2((0.5, 0.5))
            p1 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z - 0.25)) + Point2((0.5, 0.5))
            # Red
            color = Point3((255, 0, 0))
            # If value == 2: show green (= we have vision on that point)
            if value == 2:
                color = Point3((0, 255, 0))
            self.client.debug_box_out(p0, p1, color=color)

    def draw_example(self):
        # Draw green boxes around SCVs if they are gathering, yellow if they are returning cargo, red the rest
        scv: Unit
        for scv in self.workers:
            pos = scv.position3d
            p0 = Point3((pos.x - 0.25, pos.y - 0.25, pos.z + 0.25))
            p1 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z - 0.25))
            # Red
            color = Point3((255, 0, 0))
            if scv.is_gathering:
                color = Point3((0, 255, 0))
            elif scv.is_returning:
                color = Point3((255, 255, 0))
            self.client.debug_box_out(p0, p1, color=color)

        # Draw lines from structures to command center
        if self.townhalls:
            cc = self.townhalls[0]
            p0 = cc.position3d
            if not self.structures:
                return
            structure: Unit
            for structure in self.structures:
                if structure == cc:
                    continue
                p1 = structure.position3d
                # Red
                color = Point3((255, 0, 0))
                self.client.debug_line_out(p0, p1, color=color)

            # Draw text on barracks
            if structure.type_id == UnitTypeId.BARRACKS:
                # Blue
                color = Point3((0, 0, 255))
                pos = structure.position3d + Point3((0, 0, 0.5))
                # TODO: Why is this text flickering
                self.client.debug_text_world(text="MY RAX", pos=pos, color=color, size=16)

        # Draw text in top left of screen
        self.client.debug_text_screen(text="Hello world!", pos=Point2((0, 0)), color=None, size=16)
        self.client.debug_text_simple(text="Hello world2!")

    def draw_facing_units(self):
        """ Draws green box on top of selected_unit2, if selected_unit2 is facing selected_unit1 """
        selected_unit1: Unit
        selected_unit2: Unit
        red = Point3((255, 0, 0))
        green = Point3((0, 255, 0))
        for selected_unit1 in (self.units | self.structures).selected:
            for selected_unit2 in self.units.selected:
                if selected_unit1 == selected_unit2:
                    continue
                if selected_unit2.is_facing_unit(selected_unit1):
                    self.client.debug_box2_out(selected_unit2, half_vertex_length=0.25, color=green)
                else:
                    self.client.debug_box2_out(selected_unit2, half_vertex_length=0.25, color=red)


def main():
    _map = random.choice(
        [
            # Most maps have 2 upper points at the ramp (len(self.main_base_ramp.upper) == 2)
            "AutomatonLE",
            "BlueshiftLE",
            "CeruleanFallLE",
            "KairosJunctionLE",
            "ParaSiteLE",
            "PortAleksanderLE",
            "StasisLE",
            "DarknessSanctuaryLE",
            "ParaSiteLE",  # Has 5 upper points at the main ramp
            "AcolyteLE",  # Has 4 upper points at the ramp to the in-base natural and 2 upper points at the small ramp
            "HonorgroundsLE",  # Has 4 or 9 upper points at the large main base ramp
        ]
    )
    _map = "PillarsofGoldLE"
    run_game(
        maps.get(_map),
        [Bot(Race.Terran, RampWallBot()), Computer(Race.Zerg, Difficulty.Hard)],
        realtime=True,
        # sc2_version="4.10.1",
    )


if __name__ == "__main__":
    main()
