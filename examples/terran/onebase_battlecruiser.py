import random
from typing import Tuple, List

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer
from sc2.player import Human
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2, Point3
from sc2.ids.unit_typeid import UnitTypeId


class BCRushBot(sc2.BotAI):
    def select_target(self) -> Tuple[Point2, bool]:
        """ Select an enemy target the units should attack. """
        targets: Units = self.enemy_structures
        if targets:
            return targets.random.position, True

        targets: Units = self.enemy_units
        if targets:
            return targets.random.position, True

        if self.units and min([u.position.distance_to(self.enemy_start_locations[0]) for u in self.units]) < 5:
            return self.enemy_start_locations[0].position, False

        return self.mineral_field.random.position, False

    async def on_step(self, iteration):
        ccs: Units = self.townhalls
        # If we no longer have townhalls, attack with all workers
        if not ccs:
            target, target_is_enemy_unit = self.select_target()
            for unit in self.workers | self.units(UnitTypeId.BATTLECRUISER):
                if not unit.is_attacking:
                    self.do(unit.attack(target))
            return
        else:
            cc: Unit = ccs.random

        # Send all BCs to attack a target.
        bcs: Units = self.units(UnitTypeId.BATTLECRUISER)
        if bcs:
            target, target_is_enemy_unit = self.select_target()
            bc: Unit
            for bc in bcs:
                # Order the BC to attack-move the target
                if target_is_enemy_unit and (bc.is_idle or bc.is_moving):
                    self.do(bc.attack(target))
                # Order the BC to move to the target, and once the select_target returns an attack-target, change it to attack-move
                elif bc.is_idle:
                    self.do(bc.move(target))

        # Build more SCVs until 22
        if self.can_afford(UnitTypeId.SCV) and self.supply_workers < 22 and cc.is_idle:
            self.do(cc.train(UnitTypeId.SCV), subtract_cost=True, subtract_supply=True)

        # Build more BCs
        if self.structures(UnitTypeId.FUSIONCORE) and self.can_afford(UnitTypeId.BATTLECRUISER):
            for sp in self.structures(UnitTypeId.STARPORT).idle:
                if sp.has_add_on:
                    if not self.can_afford(UnitTypeId.BATTLECRUISER):
                        break
                    self.do(sp.train(UnitTypeId.BATTLECRUISER), subtract_supply=True, subtract_cost=True)

        # Build more supply depots
        if self.supply_left < 6 and self.supply_used >= 14 and not self.already_pending(UnitTypeId.SUPPLYDEPOT):
            if self.can_afford(UnitTypeId.SUPPLYDEPOT):
                await self.build(UnitTypeId.SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, 8))

        # Build barracks if we have none
        if self.tech_requirement_progress(UnitTypeId.BARRACKS) == 1:
            if not self.structures(UnitTypeId.BARRACKS):
                if self.can_afford(UnitTypeId.BARRACKS):
                    await self.build(UnitTypeId.BARRACKS, near=cc.position.towards(self.game_info.map_center, 8))

            # Build refineries
            elif self.structures(UnitTypeId.BARRACKS) and self.gas_buildings.amount < 2:
                if self.can_afford(UnitTypeId.REFINERY):
                    vgs = self.vespene_geyser.closer_than(20, cc)
                    for vg in vgs:
                        if self.gas_buildings.filter(lambda unit: unit.distance_to(vg) < 1):
                            break

                        worker = self.select_build_worker(vg.position)
                        if worker is None:
                            break

                        self.do(worker.build(UnitTypeId.REFINERY, vg), subtract_cost=True)
                        break

            # Build factory if we dont have one
            if self.tech_requirement_progress(UnitTypeId.FACTORY) == 1:
                f = self.structures(UnitTypeId.FACTORY)
                if not f:
                    if self.can_afford(UnitTypeId.FACTORY):
                        await self.build(UnitTypeId.FACTORY, near=cc.position.towards(self.game_info.map_center, 8))
                # Build starport once we can build starports, up to 2
                elif (
                    f.ready
                    and self.structures.of_type({UnitTypeId.STARPORT, UnitTypeId.STARPORTFLYING}).ready.amount
                    + self.already_pending(UnitTypeId.STARPORT)
                    < 2
                ):
                    if self.can_afford(UnitTypeId.STARPORT):
                        await self.build(
                            UnitTypeId.STARPORT,
                            near=cc.position.towards(self.game_info.map_center, 15).random_on_distance(8),
                        )

        def starport_points_to_build_addon(sp_position: Point2) -> List[Point2]:
            """ Return all points that need to be checked when trying to build an addon. Returns 4 points. """
            addon_offset: Point2 = Point2((2.5, -0.5))
            addon_position: Point2 = sp_position + addon_offset
            addon_points = [
                (addon_position + Point2((x - 0.5, y - 0.5))).rounded for x in range(0, 2) for y in range(0, 2)
            ]
            return addon_points

        # Build starport techlab or lift if no room to build techlab
        sp: Unit
        for sp in self.structures(UnitTypeId.STARPORT).ready.idle:
            if not sp.has_add_on and self.can_afford(UnitTypeId.STARPORTTECHLAB):
                addon_points = starport_points_to_build_addon(sp.position)
                if all(self.in_map_bounds(addon_point) and self.in_placement_grid(addon_point) and self.in_pathing_grid(addon_point) for addon_point in addon_points):
                    self.do(sp.build(UnitTypeId.STARPORTTECHLAB), subtract_cost=True)
                else:
                    self.do(sp(AbilityId.LIFT))

        def starport_land_positions(sp_position: Point2) -> List[Point2]:
            """ Return all points that need to be checked when trying to land at a location where there is enough space to build an addon. Returns 13 points. """
            land_positions = [(sp_position + Point2((x, y))).rounded for x in range(-1, 2) for y in range(-1, 2)]
            return land_positions + starport_points_to_build_addon(sp_position)

        # Find a position to land for a flying starport so that it can build an addon
        for sp in self.structures(UnitTypeId.STARPORTFLYING).idle:
            possible_land_positions_offset = sorted(
                (Point2((x, y)) for x in range(-10, 10) for y in range(-10, 10)),
                key=lambda point: point.x**2 + point.y**2,
            )
            offset_point = Point2((-0.5, -0.5))
            possible_land_positions = (sp.position.rounded + offset_point + p for p in possible_land_positions_offset)
            for target_land_position in possible_land_positions:
                land_and_addon_points = starport_land_positions(target_land_position)
                if all(self.in_map_bounds(land_pos) and self.in_placement_grid(land_pos) and self.in_pathing_grid(land_pos) for land_pos in land_and_addon_points):
                    self.do(sp(AbilityId.LAND, target_land_position))
                    break

        # Show where it is flying to and show grid
        unit: Unit
        for sp in self.structures(UnitTypeId.STARPORTFLYING).filter(lambda unit: not unit.is_idle):
            if isinstance(sp.order_target, Point2):
                p = Point3((*sp.order_target, self.get_terrain_z_height(sp.order_target)))
                self.client.debug_box2_out(p, color=Point3((255, 0, 0)))

        # Build fusion core
        if self.structures(UnitTypeId.STARPORT).ready:
            if self.can_afford(UnitTypeId.FUSIONCORE) and not self.structures(UnitTypeId.FUSIONCORE):
                await self.build(UnitTypeId.FUSIONCORE, near=cc.position.towards(self.game_info.map_center, 8))

        # Saturate refineries
        for a in self.gas_buildings:
            if a.assigned_harvesters < a.ideal_harvesters:
                w = self.workers.closer_than(20, a)
                if w:
                    self.do(w.random.gather(a))

        # Send workers back to mine if they are idle
        for scv in self.workers.idle:
            self.do(scv.gather(self.mineral_field.closest_to(cc)))


def main():
    sc2.run_game(
        sc2.maps.get("(2)CatalystLE"),
        [
            # Human(Race.Terran),
            Bot(Race.Terran, BCRushBot()),
            Computer(Race.Zerg, Difficulty.Hard),
        ],
        realtime=False,
    )


if __name__ == "__main__":
    main()
