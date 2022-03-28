from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer


class WorkerRushBot(BotAI):

    async def on_step(self, iteration):
        if iteration == 0:
            for worker in self.workers:
                worker.attack(self.enemy_start_locations[0])


def main():
    run_game(
        maps.get("Abyssal Reef LE"),
        [Bot(Race.Zerg, WorkerRushBot()), Computer(Race.Protoss, Difficulty.Medium)],
        realtime=False,
        save_replay_as="WorkerRush.SC2Replay",
    )


if __name__ == "__main__":
    main()
