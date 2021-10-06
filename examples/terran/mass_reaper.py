""" 
Bot that stays on 1base, goes 4 rax mass reaper
This bot is one of the first examples that are micro intensive
Bot has a chance to win against elite (=Difficulty.VeryHard) zerg AI

Bot made by Burny
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
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


class MassReaperBot(BotAI):
    def __init__(self):
        # Select distance calculation method 0, which is the pure python distance calculation without caching or indexing, using math.hypot(), for more info see distances.py _distances_override_functions() function
        self.distance_calculation_method = 3

    async def on_step(self, iteration):
        # Benchmark and print duration time of the on_step method based on "self.distance_calculation_method" value
        # print(self.time_formatted, self.supply_used, self.step_time[1])
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
                            worker.build(UnitTypeId.REFINERY, vg)

                            # Dont build more than one each frame
                            break

        # Make scvs until 22, usually you only need 1:1 mineral:gas ratio for reapers, but if you don't lose any then you will need additional depots (mule income should take care of that)
        # Stop scv production when barracks is complete but we still have a command center (priotize morphing to orbital command)
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
            await self.distribute_workers()

        # Reaper micro
        enemies: Units = self.enemy_units | self.enemy_structures
        enemies_can_attack: Units = enemies.filter(lambda unit: unit.can_attack_ground)
        for r in self.units(UnitTypeId.REAPER):

            # Move to range 15 of closest unit if reaper is below 20 hp and not regenerating
            enemyThreatsClose: Units = enemies_can_attack.filter(
                lambda unit: unit.distance_to(r) < 15
            )  # Threats that can attack the reaper

            if r.health_percentage < 2 / 5 and enemyThreatsClose:
                retreatPoints: Set[Point2] = self.neighbors8(r.position,
                                                             distance=2) | self.neighbors8(r.position, distance=4)
                # Filter points that are pathable
                retreatPoints: Set[Point2] = {x for x in retreatPoints if self.in_pathing_grid(x)}
                if retreatPoints:
                    closestEnemy: Unit = enemyThreatsClose.closest_to(r)
                    retreatPoint: Unit = closestEnemy.position.furthest(retreatPoints)
                    r.move(retreatPoint)
                    continue  # Continue for loop, dont execute any of the following

            # Reaper is ready to attack, shoot nearest ground unit
            enemyGroundUnits: Units = enemies.filter(
                lambda unit: unit.distance_to(r) < 5 and not unit.is_flying
            )  # Hardcoded attackrange of 5
            if r.weapon_cooldown == 0 and enemyGroundUnits:
                enemyGroundUnits: Units = enemyGroundUnits.sorted(lambda x: x.distance_to(r))
                closestEnemy: Unit = enemyGroundUnits[0]
                r.attack(closestEnemy)
                continue  # Continue for loop, dont execute any of the following

            # Attack is on cooldown, check if grenade is on cooldown, if not then throw it to furthest enemy in range 5
            reaperGrenadeRange: float = self._game_data.abilities[AbilityId.KD8CHARGE_KD8CHARGE.value]._proto.cast_range
            enemyGroundUnitsInGrenadeRange: Units = enemies_can_attack.filter(
                lambda unit: not unit.is_structure and not unit.is_flying and unit.type_id not in
                {UnitTypeId.LARVA, UnitTypeId.EGG} and unit.distance_to(r) < reaperGrenadeRange
            )
            if enemyGroundUnitsInGrenadeRange and (r.is_attacking or r.is_moving):
                # If AbilityId.KD8CHARGE_KD8CHARGE in abilities, we check that to see if the reaper grenade is off cooldown
                abilities = await self.get_available_abilities(r)
                enemyGroundUnitsInGrenadeRange = enemyGroundUnitsInGrenadeRange.sorted(
                    lambda x: x.distance_to(r), reverse=True
                )
                furthestEnemy: Unit = None
                for enemy in enemyGroundUnitsInGrenadeRange:
                    if await self.can_cast(r, AbilityId.KD8CHARGE_KD8CHARGE, enemy, cached_abilities_of_unit=abilities):
                        furthestEnemy: Unit = enemy
                        break
                if furthestEnemy:
                    r(AbilityId.KD8CHARGE_KD8CHARGE, furthestEnemy)
                    continue  # Continue for loop, don't execute any of the following

            # Move to max unit range if enemy is closer than 4
            enemyThreatsVeryClose: Units = enemies.filter(
                lambda unit: unit.can_attack_ground and unit.distance_to(r) < 4.5
            )  # Hardcoded attackrange minus 0.5
            # Threats that can attack the reaper
            if r.weapon_cooldown != 0 and enemyThreatsVeryClose:
                retreatPoints: Set[Point2] = self.neighbors8(r.position,
                                                             distance=2) | self.neighbors8(r.position, distance=4)
                # Filter points that are pathable by a reaper
                retreatPoints: Set[Point2] = {x for x in retreatPoints if self.in_pathing_grid(x)}
                if retreatPoints:
                    closestEnemy: Unit = enemyThreatsVeryClose.closest_to(r)
                    retreatPoint: Point2 = max(
                        retreatPoints, key=lambda x: x.distance_to(closestEnemy) - x.distance_to(r)
                    )
                    r.move(retreatPoint)
                    continue  # Continue for loop, don't execute any of the following

            # Move to nearest enemy ground unit/building because no enemy unit is closer than 5
            allEnemyGroundUnits: Units = self.enemy_units.not_flying
            if allEnemyGroundUnits:
                closestEnemy: Unit = allEnemyGroundUnits.closest_to(r)
                r.move(closestEnemy)
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
    def neighbors4(self, position, distance=1) -> Set[Point2]:
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
    async def distribute_workers(self, performanceHeavy=True, onlySaturateGas=False):
        mineralTags = [x.tag for x in self.mineral_field]
        gas_buildingTags = [x.tag for x in self.gas_buildings]

        workerPool = Units([], self)
        workerPoolTags = set()

        # Find all gas_buildings that have surplus or deficit
        deficit_gas_buildings = {}
        surplusgas_buildings = {}
        for g in self.gas_buildings.filter(lambda x: x.vespene_contents > 0):
            # Only loop over gas_buildings that have still gas in them
            deficit = g.ideal_harvesters - g.assigned_harvesters
            if deficit > 0:
                deficit_gas_buildings[g.tag] = {"unit": g, "deficit": deficit}
            elif deficit < 0:
                surplusWorkers = self.workers.closer_than(10, g).filter(
                    lambda w: w not in workerPoolTags and len(w.orders) == 1 and w.orders[0].ability.id in
                    [AbilityId.HARVEST_GATHER] and w.orders[0].target in gas_buildingTags
                )
                for i in range(-deficit):
                    if surplusWorkers.amount > 0:
                        w = surplusWorkers.pop()
                        workerPool.append(w)
                        workerPoolTags.add(w.tag)
                surplusgas_buildings[g.tag] = {"unit": g, "deficit": deficit}

        # Find all townhalls that have surplus or deficit
        deficitTownhalls = {}
        surplusTownhalls = {}
        if not onlySaturateGas:
            for th in self.townhalls:
                deficit = th.ideal_harvesters - th.assigned_harvesters
                if deficit > 0:
                    deficitTownhalls[th.tag] = {"unit": th, "deficit": deficit}
                elif deficit < 0:
                    surplusWorkers = self.workers.closer_than(10, th).filter(
                        lambda w: w.tag not in workerPoolTags and len(w.orders) == 1 and w.orders[0].ability.id in
                        [AbilityId.HARVEST_GATHER] and w.orders[0].target in mineralTags
                    )
                    # workerPool.extend(surplusWorkers)
                    for i in range(-deficit):
                        if surplusWorkers.amount > 0:
                            w = surplusWorkers.pop()
                            workerPool.append(w)
                            workerPoolTags.add(w.tag)
                    surplusTownhalls[th.tag] = {"unit": th, "deficit": deficit}

            if all(
                [
                    len(deficit_gas_buildings) == 0,
                    len(surplusgas_buildings) == 0,
                    len(surplusTownhalls) == 0 or deficitTownhalls == 0,
                ]
            ):
                # Cancel early if there is nothing to balance
                return

        # Check if deficit in gas less or equal than what we have in surplus, else grab some more workers from surplus bases
        deficitGasCount = sum(
            gasInfo["deficit"] for gasTag, gasInfo in deficit_gas_buildings.items() if gasInfo["deficit"] > 0
        )
        surplusCount = sum(
            -gasInfo["deficit"] for gasTag, gasInfo in surplusgas_buildings.items() if gasInfo["deficit"] < 0
        )
        surplusCount += sum(-thInfo["deficit"] for thTag, thInfo in surplusTownhalls.items() if thInfo["deficit"] < 0)

        if deficitGasCount - surplusCount > 0:
            # Grab workers near the gas who are mining minerals
            for gTag, gInfo in deficit_gas_buildings.items():
                if workerPool.amount >= deficitGasCount:
                    break
                workersNearGas = self.workers.closer_than(10, gInfo["unit"]).filter(
                    lambda w: w.tag not in workerPoolTags and len(w.orders) == 1 and w.orders[0].ability.id in
                    [AbilityId.HARVEST_GATHER] and w.orders[0].target in mineralTags
                )
                while workersNearGas.amount > 0 and workerPool.amount < deficitGasCount:
                    w = workersNearGas.pop()
                    workerPool.append(w)
                    workerPoolTags.add(w.tag)

        # Now we should have enough workers in the pool to saturate all gases, and if there are workers left over, make them mine at townhalls that have mineral workers deficit
        for gTag, gInfo in deficit_gas_buildings.items():
            if performanceHeavy:
                # Sort furthest away to closest (as the pop() function will take the last element)
                workerPool.sort(key=lambda x: x.distance_to(gInfo["unit"]), reverse=True)
            for i in range(gInfo["deficit"]):
                if workerPool.amount > 0:
                    w = workerPool.pop()
                    if len(w.orders) == 1 and w.orders[0].ability.id in [AbilityId.HARVEST_RETURN]:
                        w.gather(gInfo["unit"], queue=True)
                    else:
                        w.gather(gInfo["unit"])

        if not onlySaturateGas:
            # If we now have left over workers, make them mine at bases with deficit in mineral workers
            for thTag, thInfo in deficitTownhalls.items():
                if performanceHeavy:
                    # Sort furthest away to closest (as the pop() function will take the last element)
                    workerPool.sort(key=lambda x: x.distance_to(thInfo["unit"]), reverse=True)
                for i in range(thInfo["deficit"]):
                    if workerPool.amount > 0:
                        w = workerPool.pop()
                        mf = self.mineral_field.closer_than(10, thInfo["unit"]).closest_to(w)
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
