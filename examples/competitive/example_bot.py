import sc2

class ExampleBot(sc2.BotAI):
    def __init__(self):
        # Improves bot performance by a little bit
        self.raw_affects_selection = True
        # The distance calculation method: 0 for raw python, 1 for scipy pdist, 2 for scipy cdist
        self.distance_calculation_method = 2

    async def on_step(self, iteration):
        # Populate this function with whatever your bot should do!
        pass

    async def on_start(self):
        print("Game started")
        # On game start or in any frame actually, you can set the game step here - do not put it in the __init__ function as the client will not have been initialized yet
        self.client.game_step = 2
        # On first step/frame, send all workers to attack the enemy start location
        for worker in self.workers:
            self.do(worker.attack(self.enemy_start_locations[0]))

    def on_end(self, result):
        print("OnGameEnd() was called.")
