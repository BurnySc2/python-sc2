import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from loguru import logger

import sc2
from sc2 import Race, Difficulty
from sc2.ids.unit_typeid import UnitTypeId
from sc2.player import Bot, Computer
from sc2.unit import Unit
from sc2.units import Units

from s2clientprotocol import raw_pb2 as raw_pb
from s2clientprotocol import sc2api_pb2 as sc_pb
from s2clientprotocol import ui_pb2 as ui_pb


class SingleUnitUnloadBot(sc2.BotAI):
    async def on_start(self):
        self.client.game_step = 8
        self.raw_affects_selection = True
        self.load_unit_types = {
            UnitTypeId.ZEALOT,
            UnitTypeId.STALKER,
            UnitTypeId.DARKTEMPLAR,
            UnitTypeId.HIGHTEMPLAR,
        }

    async def on_step(self, iteration):
        # Spawn units
        logger.info(f"Spawning units")
        await self.client.debug_create_unit(
            [
                [UnitTypeId.WARPPRISM, 1, self.game_info.map_center, 1],
                [UnitTypeId.ZEALOT, 1, self.game_info.map_center, 1],
                [UnitTypeId.STALKER, 1, self.game_info.map_center, 1],
                [UnitTypeId.DARKTEMPLAR, 1, self.game_info.map_center, 1],
                [UnitTypeId.HIGHTEMPLAR, 1, self.game_info.map_center, 1],
            ]
        )
        # Load units into prism
        await self._advance_steps(50)
        prism = self.units(UnitTypeId.WARPPRISM)[0]
        my_zealot = self.units(UnitTypeId.ZEALOT)[0]
        my_units = self.units(self.load_unit_types)
        logger.info(f"Loading units into prism: {my_units}")
        for unit in my_units:
            unit.smart(prism)

        # Unload single unit - here: zealot
        await self._advance_steps(50)
        assert self.units(self.load_unit_types).amount == 0
        prism: Unit = self.units(UnitTypeId.WARPPRISM)[0]
        zealot_index = next(
            (
                index for index, unit in enumerate(prism.passengers)
                if unit.type_id == UnitTypeId.ZEALOT and unit.tag == my_zealot.tag
            ), None
        )

        if zealot_index is not None:
            logger.info(f"Unloading unit at index: {zealot_index}")
            await self.client._execute(
                action=sc_pb.RequestAction(
                    actions=[
                        sc_pb.Action(
                            action_raw=raw_pb.ActionRaw(
                                unit_command=raw_pb.ActionRawUnitCommand(ability_id=0, unit_tags=[prism.tag])
                            )
                        ),
                        sc_pb.Action(
                            action_ui=ui_pb.ActionUI(
                                # this can't actually be reached if index hasn't been assigned a value
                                cargo_panel=ui_pb.ActionCargoPanelUnload(unit_index=zealot_index)
                            )
                        ),
                    ]
                )
            )

        await self._advance_steps(50)
        my_units = self.units(self.load_unit_types)
        assert my_units.amount == 1, f"{my_units}"
        my_zealots = self.units(UnitTypeId.ZEALOT)
        assert my_zealots.amount == 1, f"{my_zealots}"
        assert my_zealots.amount[0].tag == my_zealot.tag


def main():
    sc2.run_game(
        sc2.maps.get("2000AtmospheresAIE"),
        [Bot(Race.Protoss, SingleUnitUnloadBot()),
         Computer(Race.Terran, Difficulty.Medium)],
        realtime=False,
        save_replay_as="PvT.SC2Replay",
    )


if __name__ == "__main__":
    main()
