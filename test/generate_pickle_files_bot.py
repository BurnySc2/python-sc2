"""
This "bot" will loop over several available ladder maps and generate the pickle file in the "/test/pickle_data/" subfolder.
These will then be used to run tests from the test script "test_pickled_data.py"
"""
import lzma
import os
import pickle
from typing import Set

from loguru import logger
from s2clientprotocol import sc2api_pb2 as sc_pb

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.game_data import GameData
from sc2.game_info import GameInfo
from sc2.game_state import GameState
from sc2.ids.unit_typeid import UnitTypeId
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2.protocol import ProtocolError


class ExporterBot(BotAI):

    def __init__(self):
        BotAI.__init__(self)
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
        raw_game_data = await self.client._execute(
            data=sc_pb.RequestData(ability_id=True, unit_type_id=True, upgrade_id=True, buff_id=True, effect_id=True)
        )

        raw_game_info = await self.client._execute(game_info=sc_pb.RequestGameInfo())

        raw_observation = self.state.response_observation

        # To test if this data is convertable in the first place
        _game_data = GameData(raw_game_data.data)
        _game_info = GameInfo(raw_game_info.game_info)
        _game_state = GameState(raw_observation)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with lzma.open(file_path, "wb") as f:
            pickle.dump([raw_game_data, raw_game_info, raw_observation], f)

    async def on_start(self):
        file_path = self.get_pickle_file_path()
        logger.info(f"Saving pickle file to {self.map_name}.xz")
        await self.store_data_to_file(file_path)

        # Make map visible
        await self.client.debug_show_map()
        await self.client.debug_control_enemy()
        await self.client.debug_god()

        # Spawn one of each unit
        valid_units: Set[UnitTypeId] = {
            UnitTypeId(unit_id)
            for unit_id, data in self.game_data.units.items()
            if data._proto.race != Race.NoRace and data._proto.race != Race.Random and data._proto.available
            # Dont cloak units
            and UnitTypeId(unit_id) != UnitTypeId.MOTHERSHIP and
            (data._proto.mineral_cost or data._proto.movement_speed or data._proto.weapons)
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

        await self.client.leave()


def main():

    maps_ = [
        "16-BitLE",
        "2000AtmospheresAIE",
        "AbiogenesisLE",
        "AbyssalReefLE",
        "AcidPlantLE",
        "AcolyteLE",
        "AcropolisLE",
        "AncientCisternAIE",
        "Artana",
        "AscensiontoAiurLE",
        "AutomatonLE",
        "BackwaterLE",
        "Bandwidth",
        "BattleontheBoardwalkLE",
        "BelShirVestigeLE",
        "BerlingradAIE",
        "BlackburnAIE",
        "BlackpinkLE",
        "BlueshiftLE",
        "CactusValleyLE",
        "CatalystLE",
        "CeruleanFallLE",
        "CrystalCavern",
        "CuriousMindsAIE",
        "CyberForestLE",
        "DarknessSanctuaryLE",
        "DeathAura506",
        "DeathAuraLE",
        "DefendersLandingLE",
        "DigitalFrontier",
        "DiscoBloodbathLE",
        "DragonScalesAIE",
        "DreamcatcherLE",
        "EastwatchLE",
        "Ephemeron",
        "EphemeronLE",
        "EternalEmpire506",
        "EternalEmpireLE",
        "EverDream506",
        "EverDreamLE",
        "FractureLE",
        "FrostLE",
        "GlitteringAshesAIE",
        "GoldenauraAIE",
        "GoldenWall506",
        "GoldenWallLE",
        "GresvanAIE",
        "HardwireAIE",
        "HonorgroundsLE",
        "IceandChrome506",
        "IceandChromeLE",
        "InfestationStationAIE",
        "InsideAndOutAIE",
        "InterloperLE",
        "JagannathaAIE",
        "KairosJunctionLE",
        "KingsCoveLE",
        "LostandFoundLE",
        "LightshadeAIE",
        "MechDepotLE",
        "MoondanceAIE",
        "NeonVioletSquareLE",
        "NewkirkPrecinctTE",
        "NewRepugnancyLE",
        "NightshadeLE",
        "OdysseyLE",
        "OldSunshine",
        "OxideAIE",
        "PaladinoTerminalLE",
        "ParaSiteLE",
        "PillarsofGold506",
        "PillarsofGoldLE",
        "PortAleksanderLE",
        "PrimusQ9",
        "ProximaStationLE",
        "RedshiftLE",
        "Reminiscence",
        "RomanticideAIE",
        "RoyalBloodAIE",
        "Sanglune",
        "SequencerLE",
        "SimulacrumLE",
        "Submarine506",
        "SubmarineLE",
        "StargazersAIE",
        "StasisLE",
        "TheTimelessVoid",
        "ThunderbirdLE",
        "Treachery",
        "Triton",
        "Urzagol",
        "WaterfallAIE",
        "WintersGateLE",
        "WorldofSleepersLE",
        "YearZeroLE",
        "ZenLE",
    ]

    for map_ in maps_:
        try:
            bot = ExporterBot()
            bot.map_name = map_
            file_path = bot.get_pickle_file_path()
            if os.path.isfile(file_path):
                logger.warning(
                    f"Pickle file for map {map_} was already generated. Skipping. If you wish to re-generate files, please remove them first."
                )
                continue
            logger.info(f"Creating pickle file for map {map_} ...")
            run_game(maps.get(map_), [Bot(Race.Terran, bot), Computer(Race.Zerg, Difficulty.Easy)], realtime=False)
        except ProtocolError:
            # ProtocolError appears after a leave game request
            pass
        except Exception as e:
            logger.exception(f"Caught unknown exception: {e}")
            logger.error(
                f"Map {map_} could not be found, so pickle files for that map could not be generated. Error: {e}"
            )


if __name__ == "__main__":
    main()
