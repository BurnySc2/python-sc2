import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *


class TerranBot(sc2.BotAI):
    async def on_step(self, iteration):
        await self.distribute_workers()
        await self.build_supply()
        await self.build_workers()
        await self.expand()

    async def build_workers(self):
        for cc in self.townhalls(UnitTypeId.COMMANDCENTER).ready.idle:
            if self.can_afford(UnitTypeId.SCV):
                self.do(cc.train(UnitTypeId.SCV))

    async def expand(self):
        if self.townhalls(UnitTypeId.COMMANDCENTER).amount < 3 and self.can_afford(UnitTypeId.COMMANDCENTER):
            await self.expand_now()

    async def build_supply(self):
        ccs = self.townhalls(UnitTypeId.COMMANDCENTER).ready
        if ccs.exists:
            cc = ccs.first
            if self.supply_left < 4 and not self.already_pending(UnitTypeId.SUPPLYDEPOT):
                if self.can_afford(UnitTypeId.SUPPLYDEPOT):
                    await self.build(UnitTypeId.SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, 5))


run_game(maps.get("Abyssal Reef LE"), [
    Bot(Race.Terran, TerranBot()),
    Computer(Race.Protoss, Difficulty.Medium)
], realtime=False)
