import asyncio
import json
import os
from collections import deque
from multiprocessing import Process
from pathlib import Path
from typing import List, Set

from arenaclient.proxy.frontend import GameRunner
from arenaclient.proxy.server import run_server


class RunLocal:
    def __init__(self):
        self.server_process = None
        # Realtime and visualize setting, e.g. {"Realtime": False, "Visualize": False}
        self.data = {}
        # List of games, e.g. ["basic_bot,T,python,loser_bot,T,python,AcropolisLE"]
        self.games_queue = deque()
        self.runner = GameRunner()

    def start_server(self):
        if os.name == "nt":
            # Comment out for linux, TODO use import platform
            self.server_process = Process(target=run_server, args=[False])
            self.server_process.daemon = True
            self.server_process.start()

    def stop_server(self):
        if os.name == "nt":
            self.server_process.terminate()

    def __enter__(self):
        self.start_server()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_server()

    def add_games_to_queue(self, games: List[str]):
        for game in games:
            self.games_queue.append(game)

    def read_ladderbots(self, directory: Path, exclude_names: Set[str]):
        botdir: Path
        bots: List[str] = []
        for botdir in [x for x in directory.iterdir() if x.is_dir()]:
            for file in [x for x in botdir.iterdir() if x.is_file()]:
                if str(file).endswith("ladderbots.json"):
                    with open(str(file)) as f:
                        contents = json.load(f)
                        bots_data: dict = contents["Bots"]
                        for bot_name, bot_data in bots_data.items():
                            if bot_name.lower() in exclude_names:
                                continue
                            bot_race = bot_data["Race"][0]
                            bot_type = bot_data["Type"]
                            bots.append(",".join([bot_name, bot_race, bot_type]))
                            break
        return bots

    def generate_games_list(self, bot1_list: List[str], bot2_list: List[str], map_list: List[str]) -> List[str]:
        """
        Generates games list, every bot from 'bot1_list' will be matched against every bot from 'bot2_list' on every map in 'map_list'.

        Example input:
            generate_games_list(["CreepyBot,Z,python"], ["basic_bot,T,python", "loser_bot,T,python], ["AcropolisLE", "TritonLE"])
        """
        games = []
        for bot1_string in bot1_list:
            for bot2_string in bot2_list:
                for map_name in map_list:
                    games.append(",".join([bot1_string, bot2_string, map_name]))
        return games

    async def run_local_games(self):
        while self.games_queue:
            games = [self.games_queue.popleft()]
            await self.runner.run_local_game(games, self.data)


async def main():
    # Alternatively you can use start_server() and stop_server()
    with RunLocal() as run_local:
        # Not needed, default: realtime=False and visualize=False
        run_local.data = {"Realtime": False, "Visualize": False}

        # If you want to let your bot play vs multiple bots, edit the following
        # path = Path("/root") / "StarCraftII" / "Bots"
        # bot1_list = ["CreepyBot,Z,python"]
        # bot2_list = run_local.read_ladderbots(path, exclude_names={"creepybot", "basic_bot", "loser_bot"})
        # print(f"Generated bot2_list: {bot2_list}")

        bot1_list = ["loser_bot,Z,python"]
        bot2_list = ["basic_bot,Z,python"]
        map_list = ["TritonLE"]
        """
            "python": ["run.py", "Python"],
            "cppwin32": [f"{bot_name}.exe", "Wine"],
            "cpplinux": [f"{bot_name}", "BinaryCpp"],
            "dotnetcore": [f"{bot_name}.dll", "DotNetCore"],
            "java": [f"{bot_name}.jar", "Java"],
            "nodejs": ["main.jar", "NodeJS"],
            "Python": ["run.py", "Python"],
            "Wine": [f"{bot_name}.exe", "Wine"],
            "BinaryCpp": [f"{bot_name}", "BinaryCpp"],
            "DotNetCore": [f"{bot_name}.dll", "DotNetCore"],
            "Java": [f"{bot_name}.jar", "Java"],
            "NodeJS": ["main.jar", "NodeJS"],
        """
        # Generates all possible map and bot combinations
        games = run_local.generate_games_list(bot1_list, bot2_list, map_list)

        # If you only want to play a specific game:
        # games = ["basic_bot,T,python,loser_bot,T,python,AcropolisLE"]

        # Add games to queue
        run_local.add_games_to_queue(games)

        await run_local.run_local_games()


if __name__ == "__main__":
    asyncio.run(main())
