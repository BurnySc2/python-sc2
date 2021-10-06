""" DEPRECATED - see debug examples in terran/ramp_wall.py """
from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer


class MyBot(BotAI):
    async def on_step(self, iteration):
        for structure in self.structures:
            self._client.debug_text_world(
                "\n".join(
                    [
                        f"{structure.type_id.name}:{structure.type_id.value}",
                        f"({structure.position.x:.2f},{structure.position.y:.2f})",
                        f"{structure.build_progress:.2f}",
                    ] + [repr(x) for x in structure.orders]
                ),
                structure.position3d,
                color=(0, 255, 0),
                size=12,
            )


def main():
    run_game(
        maps.get("Abyssal Reef LE"),
        [Bot(Race.Terran, MyBot()), Computer(Race.Protoss, Difficulty.Medium)],
        realtime=True,
    )


if __name__ == "__main__":
    main()
