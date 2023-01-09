"""
This bot attempts to stack workers 'perfectly'.
This is only a demo that works on game start, but does not work when adding more workers or bases.

This bot exists only to showcase how to keep track of mineral tag over multiple steps / frames.

Task for the user who wants to enhance this bot:
- Allow mining from vespene geysirs
- Remove dead workers and re-assign (new) workers to that mineral patch, or pick a worker from a long distance mineral patch
- Re-assign workers when new base is completed (or near complete)
- Re-assign workers when base died
- Re-assign workers when mineral patch mines out
- Re-assign workers when gas mines out
"""

from typing import Dict, Set

from loguru import logger

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units


# pylint: disable=W0231
class WorkerStackBot(BotAI):

    def __init__(self):
        self.worker_to_mineral_patch_dict: Dict[int, int] = {}
        self.mineral_patch_to_list_of_workers: Dict[int, Set[int]] = {}
        self.minerals_sorted_by_distance: Units = Units([], self)
        # Distance 0.01 to 0.1 seems fine
        self.townhall_distance_threshold = 0.01
        # Distance factor between 0.95 and 1.0 seems fine
        self.townhall_distance_factor = 1

    async def on_start(self):
        self.client.game_step = 1
        await self.assign_workers()

    async def assign_workers(self):
        self.minerals_sorted_by_distance = self.mineral_field.closer_than(10,
                                                                          self.start_location).sorted_by_distance_to(
                                                                              self.start_location
                                                                          )

        # Assign workers to mineral patch, start with the mineral patch closest to base
        for mineral in self.minerals_sorted_by_distance:
            # Assign workers closest to the mineral patch
            workers = self.workers.tags_not_in(self.worker_to_mineral_patch_dict).sorted_by_distance_to(mineral)
            for worker in workers:
                # Assign at most 2 workers per patch
                # This dict is not really used further down the code, but useful to keep track of how many workers are assigned to this mineral patch - important for when the mineral patch mines out or a worker dies
                if len(self.mineral_patch_to_list_of_workers.get(mineral.tag, [])) < 2:
                    if len(self.mineral_patch_to_list_of_workers.get(mineral.tag, [])) == 0:
                        self.mineral_patch_to_list_of_workers[mineral.tag] = {worker.tag}
                    else:
                        self.mineral_patch_to_list_of_workers[mineral.tag].add(worker.tag)
                    # Keep track of which mineral patch the worker is assigned to - if the mineral patch mines out, reassign the worker to another patch
                    self.worker_to_mineral_patch_dict[worker.tag] = mineral.tag
                else:
                    break

    async def on_step(self, iteration: int):
        if self.worker_to_mineral_patch_dict:
            # Quick-access cache mineral tag to mineral Unit
            minerals: Dict[int, Unit] = {mineral.tag: mineral for mineral in self.mineral_field}

            for worker in self.workers:
                if not self.townhalls:
                    logger.error("All townhalls died - can't return resources")
                    break

                worker: Unit
                mineral_tag = self.worker_to_mineral_patch_dict[worker.tag]
                mineral = minerals.get(mineral_tag, None)
                if mineral is None:
                    logger.error(f"Mined out mineral with tag {mineral_tag} for worker {worker.tag}")
                    continue

                # Order worker to mine at target mineral patch if isn't carrying minerals
                if not worker.is_carrying_minerals:
                    if not worker.is_gathering or worker.order_target != mineral.tag:
                        worker.gather(mineral)
                # Order worker to return minerals if carrying minerals
                else:
                    th = self.townhalls.closest_to(worker)
                    # Move worker in front of the nexus to avoid deceleration until the last moment
                    if worker.distance_to(th) > th.radius + worker.radius + self.townhall_distance_threshold:
                        pos: Point2 = th.position
                        worker.move(pos.towards(worker, th.radius * self.townhall_distance_factor))
                        worker.return_resource(queue=True)
                    else:
                        worker.return_resource()
                        worker.gather(mineral, queue=True)

        # Print info every 30 game-seconds
        if self.state.game_loop % (22.4 * 30) == 0:
            logger.info(f"{self.time_formatted} Mined a total of {int(self.state.score.collected_minerals)} minerals")


def main():
    run_game(
        maps.get("AcropolisLE"),
        [Bot(Race.Protoss, WorkerStackBot()),
         Computer(Race.Terran, Difficulty.Medium)],
        realtime=False,
        random_seed=0,
    )


if __name__ == "__main__":
    main()
