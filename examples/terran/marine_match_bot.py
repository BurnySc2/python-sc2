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

        self.marine_tag_list, self.marine_friendly_tag_list, self.marine_enemy_tag_list = build_ordered_marine_tag_list(
            self)

        attack_nearest_max_allocation(self, max_allocation=self.max_allocation)

        marine_health_dict, are_there_friendly_marines, are_there_enemy_marines = observe_health(self, marine_tag_list=self.marine_tag_list)

        self.report_data = pd.DataFrame(marine_health_dict, index=[0])

        if self.meta_meta_run_number is not None:
            async with aiofiles.open(f"new_file{self.meta_meta_run_number}.csv", mode="w", encoding="utf-8", newline="") as afp:
                writer = AsyncDictWriter(afp, self.report_data.columns, restval="NULL", quoting=csv.QUOTE_ALL)
                await writer.writeheader()
                await writer.writerows(self.report_data.to_dict(orient='records'))

        self.event_dict['started'].set()

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

        attack_nearest_max_allocation(self, max_allocation=self.max_allocation)

        marine_health_dict, are_there_friendly_marines, are_there_enemy_marines = observe_health(
            self, marine_tag_list=self.marine_tag_list
        )

        self.report_data.loc[curr_time] = marine_health_dict

        self.report_data.fillna(0.0, inplace=True)

        if self.meta_meta_run_number is not None:
            async with aiofiles.open(f"new_file{self.meta_meta_run_number}.csv", mode="w", encoding="utf-8", newline="") as afp:
                writer = AsyncDictWriter(afp, self.report_data.columns, restval="NULL", quoting=csv.QUOTE_ALL)
                await writer.writeheader()
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
