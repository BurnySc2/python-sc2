from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units


class CyclonePush(BotAI):

    def select_target(self) -> Point2:
        # Pick a random enemy structure's position
        targets = self.enemy_structures
        if targets:
            return targets.random.position

        # Pick a random enemy unit's position
        targets = self.enemy_units
        if targets:
            return targets.random.position

        # Pick enemy start location if it has no friendly units nearby
        if min((unit.distance_to(self.enemy_start_locations[0]) for unit in self.units)) > 5:
            return self.enemy_start_locations[0]

        # Pick a random mineral field on the map
        return self.mineral_field.random.position

    # pylint: disable=R0912
    async def on_step(self, iteration):
        CCs: Units = self.townhalls(UnitTypeId.COMMANDCENTER)
        # If no command center exists, attack-move with all workers and cyclones
        if not CCs:
            target = self.structures.random_or(self.enemy_start_locations[0]).position
            for unit in self.workers | self.units(UnitTypeId.CYCLONE):
                unit.attack(target)
            return

        # Otherwise, grab the first command center from the list of command centers
        cc: Unit = CCs.first

        # Every 50 iterations (here: every 50*8 = 400 frames)
        if iteration % 50 == 0 and self.units(UnitTypeId.CYCLONE).amount > 2:
            target: Point2 = self.select_target()
            forces: Units = self.units(UnitTypeId.CYCLONE)
            # Every 4000 frames: send all forces to attack-move the target position
            if iteration % 500 == 0:
                for unit in forces:
                    unit.attack(target)
            # Every 400 frames: only send idle forces to attack the target position
            else:
                for unit in forces.idle:
                    unit.attack(target)

        # While we have less than 22 workers: build more
        # Check if we can afford them (by minerals and by supply)
        if (
            self.can_afford(UnitTypeId.SCV) and self.supply_workers + self.already_pending(UnitTypeId.SCV) < 22
            and cc.is_idle
        ):
            cc.train(UnitTypeId.SCV)

        # Build supply depots if we are low on supply, do not construct more than 2 at a time
        elif self.supply_left < 3:
            if self.can_afford(UnitTypeId.SUPPLYDEPOT) and self.already_pending(UnitTypeId.SUPPLYDEPOT) < 2:
                # This picks a near-random worker to build a depot at location
                # 'from command center towards game center, distance 8'
                await self.build(UnitTypeId.SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, 8))

        # If we have supply depots (careful, lowered supply depots have a different UnitTypeId: UnitTypeId.SUPPLYDEPOTLOWERED)
        if self.structures(UnitTypeId.SUPPLYDEPOT):
            # If we have no barracks
            if not self.structures(UnitTypeId.BARRACKS):
                # If we can afford barracks
                if self.can_afford(UnitTypeId.BARRACKS):
                    # Near same command as above with the depot
                    await self.build(UnitTypeId.BARRACKS, near=cc.position.towards(self.game_info.map_center, 8))

            # If we have a barracks (complete or under construction) and less than 2 gas structures (here: refineries)
            elif self.structures(UnitTypeId.BARRACKS) and self.gas_buildings.amount < 2:
                if self.can_afford(UnitTypeId.REFINERY):
                    # All the vespene geysirs nearby, including ones with a refinery on top of it
                    vgs = self.vespene_geyser.closer_than(10, cc)
                    for vg in vgs:
                        if self.gas_buildings.filter(lambda unit: unit.distance_to(vg) < 1):
                            continue
                        # Select a worker closest to the vespene geysir
                        worker: Unit = self.select_build_worker(vg)
                        # Worker can be none in cases where all workers are dead
                        # or 'select_build_worker' function only selects from workers which carry no minerals
                        if worker is None:
                            continue
                        # Issue the build command to the worker, important: vg has to be a Unit, not a position
                        worker.build_gas(vg)
                        # Only issue one build geysir command per frame
                        break

            # If we have at least one barracks that is compelted, build factory
            if self.structures(UnitTypeId.BARRACKS).ready:
                if self.structures(UnitTypeId.FACTORY).amount < 3 and not self.already_pending(UnitTypeId.FACTORY):
                    if self.can_afford(UnitTypeId.FACTORY):
                        position: Point2 = cc.position.towards_with_random_angle(self.game_info.map_center, 16)
                        await self.build(UnitTypeId.FACTORY, near=position)

        for factory in self.structures(UnitTypeId.FACTORY).ready.idle:
            # Reactor allows us to build two at a time
            if self.can_afford(UnitTypeId.CYCLONE):
                factory.train(UnitTypeId.CYCLONE)

        # Saturate gas
        for refinery in self.gas_buildings:
            if refinery.assigned_harvesters < refinery.ideal_harvesters:
                worker: Units = self.workers.closer_than(10, refinery)
                if worker:
                    worker.random.gather(refinery)

        for scv in self.workers.idle:
            scv.gather(self.mineral_field.closest_to(cc))


def main():
    run_game(
        maps.get("(2)CatalystLE"),
        [
            # Human(Race.Terran),
            Bot(Race.Terran, CyclonePush()),
            Computer(Race.Zerg, Difficulty.Easy),
        ],
        realtime=False,
        sc2_version="4.7",
    )


if __name__ == "__main__":
    main()
