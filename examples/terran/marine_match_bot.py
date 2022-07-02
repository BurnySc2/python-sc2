import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

# https://www.youtube.com/watch?v=1-QtVxce44k&ab_channel=Altercate

from marine_helper_funcs import *


class MarineBot(BotAI):
    def __init__(self, max_allocation, result=None, history_dict=None, run_index=None, meta_meta_run_number=None):
        super(MarineBot, self).__init__()
        self.event_dict = {
            'pre_started' : asyncio.Event(),
            'started': asyncio.Event()
        }

        self.max_allocation = max_allocation
        self.result = result
        self.report_data = pd.DataFrame()
        self.history_dict = history_dict
        self.run_index = run_index
        self.meta_meta_run_number = meta_meta_run_number

    async def on_start(self):
        print('on_start has been called!')

        self.start_timer = time.perf_counter()
        self.on_step_time_list = [self.start_timer]

        marine_health_dict = {}
        self.marine_tags_list = []
        # for marine in self.units(UnitTypeId.MARINE):
        #     marine.attack(
        #         self.enemy_units.closest_n_units(self.start_location, n=1)[0]
        #     )
        #     marine_health_dict[marine.tag] = marine.health
        #     self.marine_tags_list.append(marine.tag)
        #marine_health_dict = attack_nearest(self, marine_health_dict)

        #marine_health_dict = attack_nearest_max_allocation(self, marine_health_dict, max_allocation=self.max_allocation)

        self.marine_tag_list, self.marine_friendly_tag_list, self.marine_enemy_tag_list = build_ordered_marine_tag_list(
            self)

        attack_nearest_max_allocation(self, max_allocation=self.max_allocation)

        marine_health_dict, are_there_friendly_marines, are_there_enemy_marines = observe_health(self, marine_tag_list=self.marine_tag_list)

        # enemy_marine_health_dict = {}
        # self.enemy_marine_tags_list = []
        # for enemy_marine in self.enemy_units(UnitTypeId.MARINE):
        #     enemy_marine_health_dict[enemy_marine.tag] = enemy_marine.health
        #     self.enemy_marine_tags_list.append(enemy_marine.tag)

        # self.report_data = pd.DataFrame(
        #     data=marine_health_dict,
        #     index=[0]
        # ).join(
        #     pd.DataFrame(
        #         data=enemy_marine_health_dict,
        #         index=[0]
        #     )
        # )
        self.report_data = pd.DataFrame(marine_health_dict, index=[0])

        if self.meta_meta_run_number is not None:
            async with aiofiles.open(f"new_file{self.meta_meta_run_number}.csv", mode="w", encoding="utf-8", newline="") as afp:
                writer = AsyncDictWriter(afp, self.report_data.columns, restval="NULL", quoting=csv.QUOTE_ALL)
                await writer.writeheader()
                # await writer.writerows([
                #     {"name": "Sasha", "age": 42},
                #     {"name": "Hana"}
                # ])
                await writer.writerows(self.report_data.to_dict(orient='records'))

        self.event_dict['started'].set()
        # self.client.game_step = 2
        # for overlord in self.units(UnitTypeId.OVERLORD):
        #     overlord.attack(
        #         self.enemy_structures.not_flying.random_or(self.enemy_start_locations[0]).position
        #     )

    async def on_step(self, iteration):
        are_there_friendly_marines = False
        are_there_enemy_marines = False
        if not self.event_dict['started'].is_set():
            print('waiting for on_start to happen')
            await self.event_dict['started'].wait()
        curr_time = time.perf_counter()
        print('time diff - '+str(curr_time - self.on_step_time_list[-1]))
        self.on_step_time_list.append(
            curr_time
        )

        marine_health_dict = {}

        # for marine in self.units(UnitTypeId.MARINE):
        #     marine.attack(
        #         self.enemy_units.closest_n_units(self.start_location, n=1)[0]
        #     )
        #     marine_health_dict[marine.tag] = marine.health
        #     are_there_friendly_marines = True
        #marine_health_dict = attack_nearest_max_allocation(self, marine_health_dict, max_allocation=self.max_allocation)

        attack_nearest_max_allocation(self, max_allocation=self.max_allocation)

        # for marine in self.units(UnitTypeId.MARINE):
        #     are_there_friendly_marines = True
        #
        # enemy_marine_health_dict = {}
        # for enemy_marine in self.enemy_units(UnitTypeId.MARINE):
        #     enemy_marine_health_dict[enemy_marine.tag] = enemy_marine.health
        #     are_there_enemy_marines = True
        #
        # marine_health_dict.update(enemy_marine_health_dict)

        marine_health_dict, are_there_friendly_marines, are_there_enemy_marines = observe_health(
            self, marine_tag_list=self.marine_tag_list
        )

        self.report_data.loc[curr_time] = marine_health_dict

        self.report_data.fillna(0.0, inplace=True)

        if self.meta_meta_run_number is not None:
            async with aiofiles.open(f"new_file{self.meta_meta_run_number}.csv", mode="w", encoding="utf-8", newline="") as afp:
                writer = AsyncDictWriter(afp, self.report_data.columns, restval="NULL", quoting=csv.QUOTE_ALL)
                await writer.writeheader()
                # await writer.writerows([
                #     {"name": "Sasha", "age": 42},
                #     {"name": "Hana"}
                # ])
                await writer.writerows(self.report_data.to_dict(orient='records'))

        # if friendly or enemy marines health is 0, leave
        if (not are_there_enemy_marines) or (not are_there_friendly_marines):
            if self.history_dict is not None:
                self.history_dict[self.run_index]['report_data'] = self.report_data.to_json()

            print(self.report_data)
            print(self.report_data.iloc[-1, :].values)

            if self.result is not None:
                self.result.append(
                    calc_value_func(
                        list(
                            self.report_data.iloc[-1, :].values
                        )
                    )
                )
                print('results for this round is: '+str(self.result))

            await self.client.leave()

        # if iteration == 0:
        #     await self.chat_send("(glhf)")
        #
        # # Draw creep pixelmap for debugging
        # # self.draw_creep_pixelmap()
        #
        # # If townhall no longer exists: attack move with all units to enemy start location
        # if not self.townhalls:
        #     for unit in self.units.exclude_type({UnitTypeId.EGG, UnitTypeId.LARVA}):
        #         unit.attack(self.enemy_start_locations[0])
        #     return
        #
        # hatch: Unit = self.townhalls[0]
        #
        # # Pick a target location
        # target: Point2 = self.enemy_structures.not_flying.random_or(self.enemy_start_locations[0]).position
        #
        # # Give all zerglings an attack command
        # for zergling in self.units(UnitTypeId.ZERGLING):
        #     zergling.attack(target)
        #
        # # Inject hatchery if queen has more than 25 energy
        # for queen in self.units(UnitTypeId.QUEEN):
        #     if queen.energy >= 25 and not hatch.has_buff(BuffId.QUEENSPAWNLARVATIMER):
        #         queen(AbilityId.EFFECT_INJECTLARVA, hatch)
        #
        # # Pull workers out of gas if we have almost enough gas mined, this will stop mining when we reached 100 gas mined
        # if self.vespene >= 88 or self.already_pending_upgrade(UpgradeId.ZERGLINGMOVEMENTSPEED) > 0:
        #     gas_drones: Units = self.workers.filter(lambda w: w.is_carrying_vespene and len(w.orders) < 2)
        #     drone: Unit
        #     for drone in gas_drones:
        #         minerals: Units = self.mineral_field.closer_than(10, hatch)
        #         if minerals:
        #             mineral: Unit = minerals.closest_to(drone)
        #             drone.gather(mineral, queue=True)
        #
        # # If we have 100 vespene, this will try to research zergling speed once the spawning pool is at 100% completion
        # if self.already_pending_upgrade(UpgradeId.ZERGLINGMOVEMENTSPEED
        #                                 ) == 0 and self.can_afford(UpgradeId.ZERGLINGMOVEMENTSPEED):
        #     spawning_pools_ready: Units = self.structures(UnitTypeId.SPAWNINGPOOL).ready
        #     if spawning_pools_ready:
        #         self.research(UpgradeId.ZERGLINGMOVEMENTSPEED)
        #
        # # If we have less than 2 supply left and no overlord is in the queue: train an overlord
        # if self.supply_left < 2 and self.already_pending(UnitTypeId.OVERLORD) < 1:
        #     self.train(UnitTypeId.OVERLORD, 1)
        #
        # # While we have less than 88 vespene mined: send drones into extractor one frame at a time
        # if (
        #     self.gas_buildings.ready and self.vespene < 88
        #     and self.already_pending_upgrade(UpgradeId.ZERGLINGMOVEMENTSPEED) == 0
        # ):
        #     extractor: Unit = self.gas_buildings.first
        #     if extractor.surplus_harvesters < 0:
        #         self.workers.random.gather(extractor)
        #
        # # If we have lost of minerals, make a macro hatchery
        # if self.minerals > 500:
        #     for d in range(4, 15):
        #         pos: Point2 = hatch.position.towards(self.game_info.map_center, d)
        #         if await self.can_place_single(UnitTypeId.HATCHERY, pos):
        #             self.workers.random.build(UnitTypeId.HATCHERY, pos)
        #             break
        #
        # # While we have less than 16 drones, make more drones
        # if self.can_afford(UnitTypeId.DRONE) and self.supply_workers < 16:
        #     self.train(UnitTypeId.DRONE)
        #
        # # If our spawningpool is completed, start making zerglings
        # if self.structures(UnitTypeId.SPAWNINGPOOL).ready and self.larva and self.can_afford(UnitTypeId.ZERGLING):
        #     amount_trained: int = self.train(UnitTypeId.ZERGLING, self.larva.amount)
        #
        # # If we have no extractor, build extractor
        # if (
        #     self.gas_buildings.amount + self.already_pending(UnitTypeId.EXTRACTOR) == 0
        #     and self.can_afford(UnitTypeId.EXTRACTOR) and self.workers
        # ):
        #     drone: Unit = self.workers.random
        #     target: Unit = self.vespene_geyser.closest_to(drone)
        #     drone.build_gas(target)
        #
        # # If we have no spawning pool, try to build spawning pool
        # elif self.structures(UnitTypeId.SPAWNINGPOOL).amount + self.already_pending(UnitTypeId.SPAWNINGPOOL) == 0:
        #     if self.can_afford(UnitTypeId.SPAWNINGPOOL):
        #         for d in range(4, 15):
        #             pos: Point2 = hatch.position.towards(self.game_info.map_center, d)
        #             if await self.can_place_single(UnitTypeId.SPAWNINGPOOL, pos):
        #                 drone: Unit = self.workers.closest_to(pos)
        #                 drone.build(UnitTypeId.SPAWNINGPOOL, pos)
        #
        # # If we have no queen, try to build a queen if we have a spawning pool compelted
        # elif (
        #     self.units(UnitTypeId.QUEEN).amount + self.already_pending(UnitTypeId.QUEEN) < self.townhalls.amount
        #     and self.structures(UnitTypeId.SPAWNINGPOOL).ready
        # ):
        #     if self.can_afford(UnitTypeId.QUEEN):
        #         self.train(UnitTypeId.QUEEN)

    # def draw_creep_pixelmap(self):
    #     for (y, x), value in np.ndenumerate(self.state.creep.data_numpy):
    #         p = Point2((x, y))
    #         h2 = self.get_terrain_z_height(p)
    #         pos = Point3((p.x, p.y, h2))
    #         # Red if there is no creep
    #         color = Point3((255, 0, 0))
    #         if value == 1:
    #             # Green if there is creep
    #             color = Point3((0, 255, 0))
    #         self._client.debug_box2_out(pos, half_vertex_length=0.25, color=color)

    async def on_end(self, game_result: Result):
        #self.report_data.to_csv('./marine_focus_fire_data/marine_health_data.csv')
        print(f"{self.time_formatted} On end was called")


def main():
    run_game(
        maps.get("Blistering Sands_marines2"),  # maps.get("marines_4x4"), #maps.get("Blistering Sands_marines"),
        [Bot(Race.Terran, MarineBot(max_allocation=6)), Computer(Race.Terran, Difficulty.VeryEasy)],
        realtime=True,
        #save_replay_as="ZvT.SC2Replay",
        disable_fog=True
    )


if __name__ == "__main__":
    #main()
    import time

    start = time.time()
    print("hello")
    main()
    end = time.time()
    print(end - start)
