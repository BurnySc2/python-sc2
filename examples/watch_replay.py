import os
from sc2.observer_ai import ObserverAI
from sc2 import run_replay


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
    if os.path.isabs(replay_name):
        replay_path = replay_name
    else:
        # Convert relative path to absolute path, assuming this replay is in this folder
        folder_path = os.path.dirname(__file__)
        replay_path = os.path.join(folder_path, replay_name)
    assert os.path.isfile(
        replay_path
    ), f"Run worker_rush.py in the same folder first to generate a replay. Then run watch_replay.py again."
    run_replay(my_observer_ai, replay_path=replay_path)
