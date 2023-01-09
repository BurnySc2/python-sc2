"""
Bot that stays on 1base, goes 4 rax mass reaper
This bot is one of the first examples that are micro intensive
Bot has a chance to win against elite (=Difficulty.VeryHard) zerg AI

Bot made by Burny
"""

import random
from typing import Set

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units


# pylint: disable=W0231
class MassReaperBot(BotAI):

    def __init__(self):
        # Select distance calculation method 0, which is the pure python distance calculation without caching or indexing, using math.hypot(), for more info see bot_ai_internal.py _distances_override_functions() function
        self.distance_calculation_method = 3

    # pylint: disable=R0912,R0914
    async def on_step(self, iteration):
        # Benchmark and print duration time of the on_step method based on "self.distance_calculation_method" value
        # logger.info(self.time_formatted, self.supply_used, self.step_time[1])
        """
        - build depots when low on remaining supply
        - townhalls contains commandcenter and orbitalcommand
        - self.units(TYPE).not_ready.amount selects all units of that type, filters incomplete units, and then counts the amount
        - self.already_pending(TYPE) counts how many units are queued
        """
        if (
            self.supply_left < 5 and self.townhalls and self.supply_used >= 14
            and self.can_afford(UnitTypeId.SUPPLYDEPOT) and self.already_pending(UnitTypeId.SUPPLYDEPOT) < 1
        ):
            workers: Units = self.workers.gathering
            # If workers were found
            if workers:
                worker: Unit = workers.furthest_to(workers.center)
                location: Point2 = await self.find_placement(UnitTypeId.SUPPLYDEPOT, worker.position, placement_step=3)
                # If a placement location was found
                if location:
                    # Order worker to build exactly on that location
                    worker.build(UnitTypeId.SUPPLYDEPOT, location)

        # Lower all depots when finished
        for depot in self.structures(UnitTypeId.SUPPLYDEPOT).ready:
            depot(AbilityId.MORPH_SUPPLYDEPOT_LOWER)

        # Morph commandcenter to orbitalcommand
        # Check if tech requirement for orbital is complete (e.g. you need a barracks to be able to morph an orbital)
        orbital_tech_requirement: float = self.tech_requirement_progress(UnitTypeId.ORBITALCOMMAND)
        if orbital_tech_requirement == 1:
            # Loop over all idle command centers (CCs that are not building SCVs or morphing to orbital)
            for cc in self.townhalls(UnitTypeId.COMMANDCENTER).idle:
                # Check if we have 150 minerals; this used to be an issue when the API returned 550 (value) of the orbital, but we only wanted the 150 minerals morph cost
                if self.can_afford(UnitTypeId.ORBITALCOMMAND):
                    cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND)

        # Expand if we can afford (400 minerals) and have less than 2 bases
        if (
            1 <= self.townhalls.amount < 2 and self.already_pending(UnitTypeId.COMMANDCENTER) == 0
            and self.can_afford(UnitTypeId.COMMANDCENTER)
        ):
            # get_next_expansion returns the position of the next possible expansion location where you can place a command center
            location: Point2 = await self.get_next_expansion()
            if location:
                # Now we "select" (or choose) the nearest worker to that found location
                worker: Unit = self.select_build_worker(location)
                if worker and self.can_afford(UnitTypeId.COMMANDCENTER):
                    # The worker will be commanded to build the command center
                    worker.build(UnitTypeId.COMMANDCENTER, location)

        # Build up to 4 barracks if we can afford them
        # Check if we have a supply depot (tech requirement) before trying to make barracks
        barracks_tech_requirement: float = self.tech_requirement_progress(UnitTypeId.BARRACKS)
        if (
            barracks_tech_requirement == 1
            # self.structures.of_type(
            #     [UnitTypeId.SUPPLYDEPOT, UnitTypeId.SUPPLYDEPOTLOWERED, UnitTypeId.SUPPLYDEPOTDROP]
            # ).ready
            and self.structures(UnitTypeId.BARRACKS).ready.amount + self.already_pending(UnitTypeId.BARRACKS) < 4 and
            self.can_afford(UnitTypeId.BARRACKS)
        ):
            workers: Units = self.workers.gathering
            if (
                workers and self.townhalls
            ):  # need to check if townhalls.amount > 0 because placement is based on townhall location
                worker: Unit = workers.furthest_to(workers.center)
                # I chose placement_step 4 here so there will be gaps between barracks hopefully
                location: Point2 = await self.find_placement(
                    UnitTypeId.BARRACKS, self.townhalls.random.position, placement_step=4
                )
                if location:
                    worker.build(UnitTypeId.BARRACKS, location)

        # Build refineries (on nearby vespene) when at least one barracks is in construction
        if (
            self.structures(UnitTypeId.BARRACKS).ready.amount + self.already_pending(UnitTypeId.BARRACKS) > 0
            and self.already_pending(UnitTypeId.REFINERY) < 1
        ):
            # Loop over all townhalls that are 100% complete
            for th in self.townhalls.ready:
                # Find all vespene geysers that are closer than range 10 to this townhall
                vgs: Units = self.vespene_geyser.closer_than(10, th)
                for vg in vgs:
                    if await self.can_place_single(UnitTypeId.REFINERY,
                                                   vg.position) and self.can_afford(UnitTypeId.REFINERY):
                        workers: Units = self.workers.gathering
                        if workers:  # same condition as above
                            worker: Unit = workers.closest_to(vg)
                            # Caution: the target for the refinery has to be the vespene geyser, not its position!
                            worker.build_gas(vg)

                            # Dont build more than one each frame
                            break

        # Make scvs until 22, usually you only need 1:1 mineral:gas ratio for reapers, but if you don't lose any then you will need additional depots (mule income should take care of that)
        # Stop scv production when barracks is complete but we still have a command center (priotize morphing to orbital command)
    # pylint: disable=R0916
        if (
            self.can_afford(UnitTypeId.SCV) and self.supply_left > 0 and self.supply_workers < 22 and (
                self.structures(UnitTypeId.BARRACKS).ready.amount < 1 and self.townhalls(UnitTypeId.COMMANDCENTER).idle
                or self.townhalls(UnitTypeId.ORBITALCOMMAND).idle
            )
        ):
            for th in self.townhalls.idle:
                th.train(UnitTypeId.SCV)

        # Make reapers if we can afford them and we have supply remaining
        if self.supply_left > 0:
            # Loop through all idle barracks
            for rax in self.structures(UnitTypeId.BARRACKS).idle:
                if self.can_afford(UnitTypeId.REAPER):
                    rax.train(UnitTypeId.REAPER)

        # Send workers to mine from gas
        if iteration % 25 == 0:
            await self.my_distribute_workers()

        # Reaper micro
        enemies: Units = self.enemy_units | self.enemy_structures
        enemies_can_attack: Units = enemies.filter(lambda unit: unit.can_attack_ground)
        for r in self.units(UnitTypeId.REAPER):

            # Move to range 15 of closest unit if reaper is below 20 hp and not regenerating
            enemy_threats_close: Units = enemies_can_attack.filter(
                lambda unit: unit.distance_to(r) < 15
            )  # Threats that can attack the reaper

            if r.health_percentage < 2 / 5 and enemy_threats_close:
                retreat_points: Set[Point2] = self.neighbors8(r.position,
                                                              distance=2) | self.neighbors8(r.position, distance=4)
                # Filter points that are pathable
                retreat_points: Set[Point2] = {x for x in retreat_points if self.in_pathing_grid(x)}
                if retreat_points:
                    closest_enemy: Unit = enemy_threats_close.closest_to(r)
                    retreat_point: Unit = closest_enemy.position.furthest(retreat_points)
                    r.move(retreat_point)
                    continue  # Continue for loop, dont execute any of the following

            # Reaper is ready to attack, shoot nearest ground unit
            enemy_ground_units: Units = enemies.filter(
                lambda unit: unit.distance_to(r) < 5 and not unit.is_flying
            )  # Hardcoded attackrange of 5
            if r.weapon_cooldown == 0 and enemy_ground_units:
                enemy_ground_units: Units = enemy_ground_units.sorted(lambda x: x.distance_to(r))
                closest_enemy: Unit = enemy_ground_units[0]
                r.attack(closest_enemy)
                continue  # Continue for loop, dont execute any of the following

            # Attack is on cooldown, check if grenade is on cooldown, if not then throw it to furthest enemy in range 5
            # pylint: disable=W0212
            reaper_grenade_range: float = (
                self.game_data.abilities[AbilityId.KD8CHARGE_KD8CHARGE.value]._proto.cast_range
            )
            enemy_ground_units_in_grenade_range: Units = enemies_can_attack.filter(
                lambda unit: not unit.is_structure and not unit.is_flying and unit.type_id not in
                {UnitTypeId.LARVA, UnitTypeId.EGG} and unit.distance_to(r) < reaper_grenade_range
            )
            if enemy_ground_units_in_grenade_range and (r.is_attacking or r.is_moving):
                # If AbilityId.KD8CHARGE_KD8CHARGE in abilities, we check that to see if the reaper grenade is off cooldown
                abilities = await self.get_available_abilities(r)
                enemy_ground_units_in_grenade_range = enemy_ground_units_in_grenade_range.sorted(
                    lambda x: x.distance_to(r), reverse=True
                )
                furthest_enemy: Unit = None
                for enemy in enemy_ground_units_in_grenade_range:
                    if await self.can_cast(r, AbilityId.KD8CHARGE_KD8CHARGE, enemy, cached_abilities_of_unit=abilities):
                        furthest_enemy: Unit = enemy
                        break
                if furthest_enemy:
                    r(AbilityId.KD8CHARGE_KD8CHARGE, furthest_enemy)
                    continue  # Continue for loop, don't execute any of the following

            # Move to max unit range if enemy is closer than 4
            enemy_threats_very_close: Units = enemies.filter(
                lambda unit: unit.can_attack_ground and unit.distance_to(r) < 4.5
            )  # Hardcoded attackrange minus 0.5
            # Threats that can attack the reaper
            if r.weapon_cooldown != 0 and enemy_threats_very_close:
                retreat_points: Set[Point2] = self.neighbors8(r.position,
                                                              distance=2) | self.neighbors8(r.position, distance=4)
                # Filter points that are pathable by a reaper
                retreat_points: Set[Point2] = {x for x in retreat_points if self.in_pathing_grid(x)}
                if retreat_points:
                    closest_enemy: Unit = enemy_threats_very_close.closest_to(r)
                    retreat_point: Point2 = max(
                        retreat_points, key=lambda x: x.distance_to(closest_enemy) - x.distance_to(r)
                    )
                    r.move(retreat_point)
                    continue  # Continue for loop, don't execute any of the following

            # Move to nearest enemy ground unit/building because no enemy unit is closer than 5
            all_enemy_ground_units: Units = self.enemy_units.not_flying
            if all_enemy_ground_units:
                closest_enemy: Unit = all_enemy_ground_units.closest_to(r)
                r.move(closest_enemy)
                continue  # Continue for loop, don't execute any of the following

            # Move to random enemy start location if no enemy buildings have been seen
            r.move(random.choice(self.enemy_start_locations))

        # Manage idle scvs, would be taken care by distribute workers aswell
        if self.townhalls:
            for w in self.workers.idle:
                th: Unit = self.townhalls.closest_to(w)
                mfs: Units = self.mineral_field.closer_than(10, th)
                if mfs:
                    mf: Unit = mfs.closest_to(w)
                    w.gather(mf)

        # Manage orbital energy and drop mules
        for oc in self.townhalls(UnitTypeId.ORBITALCOMMAND).filter(lambda x: x.energy >= 50):
            mfs: Units = self.mineral_field.closer_than(10, oc)
            if mfs:
                mf: Unit = max(mfs, key=lambda x: x.mineral_contents)
                oc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mf)

        # When running out of mineral fields near command center, fly to next base with minerals

    # Helper functions

    # Stolen and modified from position.py

    @staticmethod
    def neighbors4(position, distance=1) -> Set[Point2]:
        p = position
        d = distance
        return {Point2((p.x - d, p.y)), Point2((p.x + d, p.y)), Point2((p.x, p.y - d)), Point2((p.x, p.y + d))}

    # Stolen and modified from position.py
    def neighbors8(self, position, distance=1) -> Set[Point2]:
        p = position
        d = distance
        return self.neighbors4(position, distance) | {
            Point2((p.x - d, p.y - d)),
            Point2((p.x - d, p.y + d)),
            Point2((p.x + d, p.y - d)),
            Point2((p.x + d, p.y + d)),
        }

    # Distribute workers function rewritten, the default distribute_workers() function did not saturate gas quickly enough
    # pylint: disable=R0912
    async def my_distribute_workers(self, performance_heavy=True, only_saturate_gas=False):
        mineral_tags = [x.tag for x in self.mineral_field]
        gas_building_tags = [x.tag for x in self.gas_buildings]

        worker_pool = Units([], self)
        worker_pool_tags = set()

        # Find all gas_buildings that have surplus or deficit
        deficit_gas_buildings = {}
        surplusgas_buildings = {}
        for g in self.gas_buildings.filter(lambda x: x.vespene_contents > 0):
            # Only loop over gas_buildings that have still gas in them
            deficit = g.ideal_harvesters - g.assigned_harvesters
            if deficit > 0:
                deficit_gas_buildings[g.tag] = {"unit": g, "deficit": deficit}
            elif deficit < 0:
                surplus_workers = self.workers.closer_than(10, g).filter(
                    lambda w: w not in worker_pool_tags and len(w.orders) == 1 and w.orders[0].ability.id in
                    [AbilityId.HARVEST_GATHER] and w.orders[0].target in gas_building_tags
                )
                for _ in range(-deficit):
                    if surplus_workers.amount > 0:
                        w = surplus_workers.pop()
                        worker_pool.append(w)
                        worker_pool_tags.add(w.tag)
                surplusgas_buildings[g.tag] = {"unit": g, "deficit": deficit}

        # Find all townhalls that have surplus or deficit
        deficit_townhalls = {}
        surplus_townhalls = {}
        if not only_saturate_gas:
            for th in self.townhalls:
                deficit = th.ideal_harvesters - th.assigned_harvesters
                if deficit > 0:
                    deficit_townhalls[th.tag] = {"unit": th, "deficit": deficit}
                elif deficit < 0:
                    surplus_workers = self.workers.closer_than(10, th).filter(
                        lambda w: w.tag not in worker_pool_tags and len(w.orders) == 1 and w.orders[0].ability.id in
                        [AbilityId.HARVEST_GATHER] and w.orders[0].target in mineral_tags
                    )
                    # worker_pool.extend(surplus_workers)
                    for _ in range(-deficit):
                        if surplus_workers.amount > 0:
                            w = surplus_workers.pop()
                            worker_pool.append(w)
                            worker_pool_tags.add(w.tag)
                    surplus_townhalls[th.tag] = {"unit": th, "deficit": deficit}

            if all(
                [
                    len(deficit_gas_buildings) == 0,
                    len(surplusgas_buildings) == 0,
                    len(surplus_townhalls) == 0 or deficit_townhalls == 0,
                ]
            ):
                # Cancel early if there is nothing to balance
                return

        # Check if deficit in gas less or equal than what we have in surplus, else grab some more workers from surplus bases
        deficit_gas_count = sum(
            gasInfo["deficit"] for gasTag, gasInfo in deficit_gas_buildings.items() if gasInfo["deficit"] > 0
        )
        surplus_count = sum(
            -gasInfo["deficit"] for gasTag, gasInfo in surplusgas_buildings.items() if gasInfo["deficit"] < 0
        )
        surplus_count += sum(
            -townhall_info["deficit"] for townhall_tag, townhall_info in surplus_townhalls.items()
            if townhall_info["deficit"] < 0
        )

        if deficit_gas_count - surplus_count > 0:
            # Grab workers near the gas who are mining minerals
            for _gas_tag, gas_info in deficit_gas_buildings.items():
                if worker_pool.amount >= deficit_gas_count:
                    break
                workers_near_gas = self.workers.closer_than(10, gas_info["unit"]).filter(
                    lambda w: w.tag not in worker_pool_tags and len(w.orders) == 1 and w.orders[0].ability.id in
                    [AbilityId.HARVEST_GATHER] and w.orders[0].target in mineral_tags
                )
                while workers_near_gas.amount > 0 and worker_pool.amount < deficit_gas_count:
                    w = workers_near_gas.pop()
                    worker_pool.append(w)
                    worker_pool_tags.add(w.tag)

        # Now we should have enough workers in the pool to saturate all gases, and if there are workers left over, make them mine at townhalls that have mineral workers deficit
        for _gas_tag, gas_info in deficit_gas_buildings.items():
            if performance_heavy:
                # Sort furthest away to closest (as the pop() function will take the last element)
                worker_pool.sort(key=lambda x: x.distance_to(gas_info["unit"]), reverse=True)
            for _ in range(gas_info["deficit"]):
                if worker_pool.amount > 0:
                    w = worker_pool.pop()
                    if len(w.orders) == 1 and w.orders[0].ability.id in [AbilityId.HARVEST_RETURN]:
                        w.gather(gas_info["unit"], queue=True)
                    else:
                        w.gather(gas_info["unit"])

        if not only_saturate_gas:
            # If we now have left over workers, make them mine at bases with deficit in mineral workers
            for townhall_tag, townhall_info in deficit_townhalls.items():
                if performance_heavy:
                    # Sort furthest away to closest (as the pop() function will take the last element)
                    worker_pool.sort(key=lambda x: x.distance_to(townhall_info["unit"]), reverse=True)
                for _ in range(townhall_info["deficit"]):
                    if worker_pool.amount > 0:
                        w = worker_pool.pop()
                        mf = self.mineral_field.closer_than(10, townhall_info["unit"]).closest_to(w)
                        if len(w.orders) == 1 and w.orders[0].ability.id in [AbilityId.HARVEST_RETURN]:
                            w.gather(mf, queue=True)
                        else:
                            w.gather(mf)


def main():
    # Multiple difficulties for enemy bots available https://github.com/Blizzard/s2client-api/blob/ce2b3c5ac5d0c85ede96cef38ee7ee55714eeb2f/include/sc2api/sc2_gametypes.h#L30
    run_game(
        maps.get("AcropolisLE"),
        [Bot(Race.Terran, MassReaperBot()), Computer(Race.Zerg, Difficulty.VeryHard)],
        realtime=False,
    )


if __name__ == "__main__":
    main()
