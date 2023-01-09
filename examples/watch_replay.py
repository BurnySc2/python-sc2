import os
import platform
from pathlib import Path

from loguru import logger

from sc2.main import run_replay
from sc2.observer_ai import ObserverAI


class ObserverBot(ObserverAI):
    """
    A replay bot that can run replays.
    Check sc2/observer_ai.py for more available functions
    """

    async def on_start(self):
        print("Replay on_start() was called")

    async def on_step(self, iteration: int):
        print(f"Replay iteration: {iteration}")


if __name__ == "__main__":
    my_observer_ai = ObserverBot()
    # Enter replay name here
    # The replay should be either in this folder and you can give it a relative path, or change it to the absolute path
    replay_name = "WorkerRush.SC2Replay"
    if platform.system() == "Linux":
        home_replay_folder = Path.home() / "Documents" / "StarCraft II" / "Replays"
        replay_path = home_replay_folder / replay_name
        if not replay_path.is_file():
            logger.warning(f"You are on linux, please put the replay in directory {home_replay_folder}")
            raise FileNotFoundError
        replay_path = str(replay_path)
    elif os.path.isabs(replay_name):
        replay_path = replay_name
    else:
        # Convert relative path to absolute path, assuming this replay is in this folder
        folder_path = os.path.dirname(__file__)
        replay_path = os.path.join(folder_path, replay_name)
    assert os.path.isfile(
        replay_path
    ), "Run worker_rush.py in the same folder first to generate a replay. Then run watch_replay.py again."
    run_replay(my_observer_ai, replay_path=replay_path)
