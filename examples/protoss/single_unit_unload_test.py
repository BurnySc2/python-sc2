import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from typing import Union
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
    def __init__(self):
        self.raw_affects_selection = True
        self.enable_feature_layer = True

    async def on_start(self):
        self.client.game_step = 8
        self.load_unit_types = {
            UnitTypeId.ZEALOT,
            UnitTypeId.STALKER,
            UnitTypeId.DARKTEMPLAR,
            UnitTypeId.HIGHTEMPLAR,
        }

    async def unload_unit(self, transporter_unit: Unit, unload_unit: Union[int, Unit]):
        assert isinstance(transporter_unit, Unit)
        assert isinstance(unload_unit, (int, Unit))
        assert hasattr(self, "raw_affects_selection") and self.raw_affects_selection is True
        assert hasattr(self, "enable_feature_layer") and self.enable_feature_layer is True
        if isinstance(unload_unit, Unit):
            unload_unit_tag = unload_unit.tag
        else:
            unload_unit_tag = unload_unit

        # TODO Change unit.py passengers to return a List[Unit] instead of Set[Unit] ? Then I don't have to loop over '._proto'
        unload_unit_index = next(
            (index for index, unit in enumerate(transporter_unit._proto.passengers) if unit.tag == unload_unit_tag),
            None
        )

        if unload_unit_index is None:
            logger.info(f"Unable to find unit {unload_unit} in transporter {transporter_unit}")
            return

        logger.info(f"Unloading unit at index: {unload_unit_index}")
        await self.client._execute(
            action=sc_pb.RequestAction(
                actions=[
                    sc_pb.Action(
                        action_raw=raw_pb.ActionRaw(
                            unit_command=raw_pb.ActionRawUnitCommand(ability_id=0, unit_tags=[transporter_unit.tag])
                        )
                    ),
                    sc_pb.Action(
                        action_ui=ui_pb.ActionUI(
                            cargo_panel=ui_pb.ActionCargoPanelUnload(unit_index=unload_unit_index)
                        )
                    ),
                ]
            )
        )

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
        await self.unload_unit(prism, my_zealot)
        # Also works:
        # await self.unload_unit(prism, my_zealot.tag)

        await self._advance_steps(50)
        my_units = self.units(self.load_unit_types)
        assert my_units.amount == 1, f"{my_units}"
        my_zealots = self.units(UnitTypeId.ZEALOT)
        assert my_zealots.amount == 1, f"{my_zealots}"
        assert my_zealots[0].tag == my_zealot.tag

        logger.info("Everything ran as expected. Terminating.")
        await self.client.leave()


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
