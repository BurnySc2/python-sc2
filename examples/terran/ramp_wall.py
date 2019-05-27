import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import random, numpy as np

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.units import Units


class RampWallBot(sc2.BotAI):
    async def on_step(self, iteration):
        cc = self.units(COMMANDCENTER)
        if not cc.exists:
            return
        else:
            cc = cc.first

        if self.can_afford(SCV) and self.workers.amount < 16 and cc.is_idle:
            await self.do(cc.train(SCV))

        # Raise depos when enemies are nearby
        for depo in self.units(SUPPLYDEPOT).ready:
            for unit in self.known_enemy_units.not_structure:
                if unit.position.to2.distance_to(depo.position.to2) < 15:
                    break
            else:
                await self.do(depo(MORPH_SUPPLYDEPOT_LOWER))

        # Lower depos when no enemies are nearby
        for depo in self.units(SUPPLYDEPOTLOWERED).ready:
            for unit in self.known_enemy_units.not_structure:
                if unit.position.to2.distance_to(depo.position.to2) < 10:
                    await self.do(depo(MORPH_SUPPLYDEPOT_RAISE))
                    break

        depot_placement_positions = self.main_base_ramp.corner_depots
        # Uncomment the following if you want to build 3 supplydepots in the wall instead of a barracks in the middle + 2 depots in the corner
        # depot_placement_positions = self.main_base_ramp.corner_depots | {self.main_base_ramp.depot_in_middle}

        barracks_placement_position = self.main_base_ramp.barracks_correct_placement
        # If you prefer to have the barracks in the middle without room for addons, use the following instead
        # barracks_placement_position = self.main_base_ramp.barracks_in_middle

        depots = self.units(SUPPLYDEPOT) | self.units(SUPPLYDEPOTLOWERED)

        # Draw ramp points
        self.draw_ramp_points()

        # Draw pathing grid
        # self.draw_pathing_grid()

        # Draw vision blockers
        # self.draw_vision_blockers()

        await self._client.send_debug()

        # # Filter locations close to finished supply depots
        if depots:
            depot_placement_positions = {d for d in depot_placement_positions if depots.closest_distance_to(d) > 1}

        # Build depots
        if self.can_afford(SUPPLYDEPOT) and not self.already_pending(SUPPLYDEPOT):
            if len(depot_placement_positions) == 0:
                return
            # Choose any depot location
            target_depot_location = depot_placement_positions.pop()
            ws = self.workers.gathering
            if ws:  # if workers were found
                w = ws.random
                await self.do(w.build(SUPPLYDEPOT, target_depot_location))

        # Build barracks
        if depots.ready and self.can_afford(BARRACKS) and not self.already_pending(BARRACKS):
            if self.units(BARRACKS).amount + self.already_pending(BARRACKS) > 0:
                return
            ws = self.workers.gathering
            if ws and barracks_placement_position:  # if workers were found
                w = ws.random
                await self.do(w.build(BARRACKS, barracks_placement_position))

    async def on_building_construction_complete(self, unit: Unit):
        print(f"Construction of building {unit} completed at {unit.position}.")

    def terrain_to_z_height(self, h):
        # Required for drawing ramp points
        return round(16 * h / 255, 2)

    def draw_ramp_points(self):
        for ramp in self.game_info.map_ramps:
            for p in ramp.points:
                h = self.get_terrain_height(p)
                h2 = self.terrain_to_z_height(h)
                pos = Point3((p.x, p.y, h2))
                p0 = Point3((pos.x - 0.25, pos.y - 0.25, pos.z))
                p1 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z - 0.5))
                # print(f"Drawing {p0} to {p1}")
                color = Point3((255, 0, 0))
                if p in ramp.upper:
                    color = Point3((0, 255, 0))
                if p in ramp.upper2_for_ramp_wall:
                    color = Point3((0, 255, 255))
                if p in ramp.lower:
                    color = Point3((0, 0, 255))
                self._client.debug_box_out(p0, p1, color=color)


    def draw_pathing_grid(self):
        map_area = self._game_info.playable_area
        for (b, a), value in np.ndenumerate(self._game_info.pathing_grid.data_numpy):
            if value == 0:
                continue
            if not (map_area.x <= a < map_area.x + map_area.width):
                continue
            if not (map_area.y <= b < map_area.y + map_area.height):
                continue
            p = Point2((a, b))
            h = self.get_terrain_height(p)
            h2 = self.terrain_to_z_height(h)
            pos = Point3((p.x, p.y, h2))
            p0 = Point3((pos.x - 0.25, pos.y - 0.25, pos.z))
            p1 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z - 0.5))
            # print(f"Drawing {p0} to {p1}")
            color = Point3((255, 0, 0))
            self._client.debug_box_out(p0, p1, color=color)

    def draw_vision_blockers(self):
        for p in self.game_info.vision_blockers:
            h = self.get_terrain_height(p)
            h2 = self.terrain_to_z_height(h)
            pos = Point3((p.x, p.y, h2))
            p0 = Point3((pos.x - 0.25, pos.y - 0.25, pos.z))
            p1 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z - 0.5))
            # print(f"Drawing {p0} to {p1}")
            color = Point3((255, 0, 0))
            self._client.debug_box_out(p0, p1, color=color)

def main():
    map = random.choice(
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
    sc2.run_game(
        sc2.maps.get(map), [Bot(Race.Terran, RampWallBot()), Computer(Race.Zerg, Difficulty.Hard)], realtime=False
    )


if __name__ == "__main__":
    main()
