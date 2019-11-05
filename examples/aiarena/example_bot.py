import sc2

class ExampleBot(sc2.BotAI):
    async def on_step(self, iteration):
        # Populate this function with whatever your bot should do!
        pass

    async def on_start(self):
        # On first step/frame, send all workers to attack the enemy start location
        print("Game started")
        for worker in self.workers:
            self.do(worker.attack(self.enemy_start_locations[0]))

    def on_end(self, result):
        print("OnGameEnd() was called.")
