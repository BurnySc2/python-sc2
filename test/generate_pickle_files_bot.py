import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import sc2
from sc2 import Race
from sc2.player import Bot

from sc2.units import Units
from sc2.unit import Unit
from sc2.position import Point2, Point3

from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.buff_id import BuffId
from sc2.ids.ability_id import AbilityId

from sc2.player import Bot, Computer
from sc2.data import Difficulty

from sc2.game_data import GameData
from sc2.game_info import GameInfo
from sc2.game_state import GameState

from sc2.protocol import ProtocolError

from typing import List, Dict, Set, Tuple, Any, Optional, Union

from s2clientprotocol import sc2api_pb2 as sc_pb
import pickle, os, sys, logging, traceback, lzma


"""
This "bot" will loop over several available ladder maps and generate the pickle file in the "/test/pickle_data/" subfolder.
These will then be used to run tests from the test script "test_pickled_data.py"
"""


class ExporterBot(sc2.BotAI):
    def __init__(self):
        sc2.BotAI.__init__(self)
        self.map_name: str = None

    async def on_step(self, iteration):
        pass

    def get_pickle_file_path(self) -> str:
        folder_path = os.path.dirname(__file__)
        subfolder_name = "pickle_data"
        file_name = f"{self.map_name}.xz"
        file_path = os.path.join(folder_path, subfolder_name, file_name)
        return file_path

    def get_combat_file_path(self) -> str:
        folder_path = os.path.dirname(__file__)
        subfolder_name = "combat_data"
        file_name = f"{self.map_name}.xz"
        file_path = os.path.join(folder_path, subfolder_name, file_name)
        return file_path

    async def store_data_to_file(self, file_path: str):
        # Grab all raw data from observation
        raw_game_data = await self._client._execute(
            data=sc_pb.RequestData(ability_id=True, unit_type_id=True, upgrade_id=True, buff_id=True, effect_id=True)
        )

        raw_game_info = await self._client._execute(game_info=sc_pb.RequestGameInfo())

        raw_observation = self.state.response_observation

        # To test if this data is convertable in the first place
        game_data = GameData(raw_game_data.data)
        game_info = GameInfo(raw_game_info.game_info)
        game_state = GameState(raw_observation)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with lzma.open(file_path, "wb") as f:
            pickle.dump([raw_game_data, raw_game_info, raw_observation], f)


    async def on_start(self):
        file_path = self.get_pickle_file_path()
        print(f"Saving file to {self.map_name}.xz")
        await self.store_data_to_file(file_path)

        # Make map visible
        await self.client.debug_show_map()
        await self.client.debug_control_enemy()
        await self.client.debug_god()

        # Spawn one of each unit
        # await self.client.debug_create_unit([[unit_id, 1, self.game_info.map_center, 1] for unit_id in self.game_data.units])
        valid_units: Set[UnitTypeId] = {
            UnitTypeId(unit_id)
            for unit_id, data in self.game_data.units.items()
            if data._proto.race != Race.NoRace and data._proto.race != Race.Random and data._proto.available
            # Dont cloak units
            and UnitTypeId(unit_id) != UnitTypeId.MOTHERSHIP
            and (data._proto.mineral_cost or data._proto.movement_speed or data._proto.weapons)
        }

        # Create units for self
        await self.client.debug_create_unit([[valid_unit, 1, self.start_location, 1] for valid_unit in valid_units])
        # Create units for enemy
        await self.client.debug_create_unit(
            [[valid_unit, 1, self.enemy_start_locations[0], 2] for valid_unit in valid_units]
        )

        await self._advance_steps(2)

        file_path = self.get_combat_file_path()
        await self.store_data_to_file(file_path)

        await self._client.leave()
        return


def main():

    maps = [
        "16-BitLE",
        "AbiogenesisLE",
        "AbyssalReefLE",
        "AcidPlantLE",
        "AcolyteLE",
        "Acropolis",
        "AcropolisLE",
        "Artana",
        "AscensiontoAiurLE",
        "AutomatonLE",
        "BackwaterLE",
        "Bandwidth",
        "BattleontheBoardwalkLE",
        "BelShirVestigeLE",
        "BlackpinkLE",
        "BloodBoilLE",
        "BlueshiftLE",
        "CactusValleyLE",
        "CatalystLE",
        "CeruleanFallLE",
        "CrystalCavern",
        "CyberForestLE",
        "DarknessSanctuaryLE",
        "DefendersLandingLE",
        "DigitalFrontier",
        "DiscoBloodbathLE",
        "DreamcatcherLE",
        "EastwatchLE",
        "Ephemeron",
        "EphemeronLE",
        "FractureLE",
        "FrostLE",
        "HonorgroundsLE",
        "InterloperLE",
        "KairosJunctionLE",
        "KingsCoveLE",
        "LostandFoundLE",
        "MechDepotLE",
        "NeonVioletSquareLE",
        "NewkirkPrecinctTE",
        "NewRepugnancyLE",
        "OdysseyLE",
        "OldSunshine",
        "PaladinoTerminalLE",
        "ParaSiteLE",
        "PortAleksanderLE",
        "PrimusQ9",
        "ProximaStationLE",
        "RedshiftLE",
        "Reminiscence",
        "Sanglune",
        "SequencerLE",
        # "StasisLE", Commented out because it has uneven number of expansions, and wasn't used in the ladder pool anyway
        "TheTimelessVoid",
        "ThunderbirdLE",
        "Treachery",
        "Triton",
        "Urzagol",
        "WintersGateLE",
        "WorldofSleepersLE",
        "YearZeroLE",
    ]

    for map_ in maps:
        logger = logging.getLogger()
        try:
            bot = ExporterBot()
            bot.map_name = map_
            file_path = bot.get_pickle_file_path()
            if os.path.isfile(file_path):
                logger.warning(
                    f"Pickle file for map {map_} was already generated. Skipping. If you wish to re-generate files, please remove them first."
                )
                continue
            sc2.run_game(
                sc2.maps.get(map_), [Bot(Race.Terran, bot), Computer(Race.Zerg, Difficulty.Easy)], realtime=False
            )
        except ProtocolError:
            # ProtocolError appears after a leave game request
            pass
        except Exception as e:
            logger.warning(
                f"Map {map_} could not be found, so pickle files for that map could not be generated. Error: {e}"
            )
            # traceback.print_exc()


if __name__ == "__main__":
    main()
