from sc2.bot_ai import BotAI
from sc2.data import Result


class CompetitiveBot(BotAI):
    # pylint: disable=R0201
    async def on_start(self):
        print("Game started")
        # Do things here before the game starts

    async def on_step(self, iteration):
        # Populate this function with whatever your bot should do!
        pass

    # pylint: disable=R0201
    def on_end(self, _result: Result):
        print("Game ended.")
        # Do things here after the game ends
