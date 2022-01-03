from sc2.bot_ai import BotAI


class CompetitiveBot(BotAI):
    async def on_start(self):
        print("Game started")
        # Do things here before the game starts

    async def on_step(self, iteration):
        # Populate this function with whatever your bot should do!
        pass

    def on_end(self, result):
        print("Game ended.")
        # Do things here after the game ends
