import random
from collections import OrderedDict

import os, subprocess

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer
from sc2.data import Alliance
from sc2.data import Target, ActionResult

from sc2.position import Pointlike, Point2, Point3
from sc2.units import Units
from sc2.unit import Unit

from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.effect_id import EffectId

from typing import Dict, List, Tuple, Union, Optional, Set

# from sc2.ids.unit_typeid import (
#     ADEPT,
#     ADEPTPHASESHIFT,
#     ARCHON,
#     ARMORY,
#     ASSIMILATOR,
#     AUTOTURRET,
#     BANELING,
#     BANELINGBURROWED,
#     BANELINGCOCOON,
#     BANELINGNEST,
#     BANSHEE,
#     BARRACKS,
#     BARRACKSFLYING,
#     BARRACKSREACTOR,
#     BARRACKSTECHLAB,
#     BATTLECRUISER,
#     BROODLING,
#     BROODLORD,
#     BROODLORDCOCOON,
#     BUNKER,
#     CARRIER,
#     CHANGELING,
#     CHANGELINGMARINE,
#     CHANGELINGMARINESHIELD,
#     CHANGELINGZEALOT,
#     CHANGELINGZERGLING,
#     CHANGELINGZERGLINGWINGS,
#     COLOSSUS,
#     COMMANDCENTER,
#     COMMANDCENTERFLYING,
#     CORRUPTOR,
#     CREEPTUMOR,
#     CREEPTUMORBURROWED,
#     CREEPTUMORQUEEN,
#     CYBERNETICSCORE,
#     CYCLONE,
#     DARKSHRINE,
#     DARKTEMPLAR,
#     DISRUPTOR,
#     DISRUPTORPHASED,
#     DRONE,
#     DRONEBURROWED,
#     EGG,
#     ENGINEERINGBAY,
#     EVOLUTIONCHAMBER,
#     EXTRACTOR,
#     FACTORY,
#     FACTORYFLYING,
#     FACTORYREACTOR,
#     FACTORYTECHLAB,
#     FLEETBEACON,
#     FORGE,
#     FUSIONCORE,
#     GATEWAY,
#     GHOST,
#     GHOSTACADEMY,
#     GREATERSPIRE,
#     HATCHERY,
#     HELLION,
#     HELLIONTANK,
#     HIGHTEMPLAR,
#     HIVE,
#     HYDRALISK,
#     HYDRALISKBURROWED,
#     HYDRALISKDEN,
#     IMMORTAL,
#     INFESTATIONPIT,
#     INFESTEDTERRANSEGG,
#     INFESTOR,
#     INFESTORBURROWED,
#     INFESTORTERRAN,
#     INFESTORTERRANBURROWED,
#     INTERCEPTOR,
#     KD8CHARGE,
#     LAIR,
#     LARVA,
#     LIBERATOR,
#     LIBERATORAG,
#     LOCUSTMP,
#     LOCUSTMPFLYING,
#     LURKERDENMP,
#     LURKERMP,
#     LURKERMPBURROWED,
#     LURKERMPEGG,
#     MARAUDER,
#     MARINE,
#     MEDIVAC,
#     MISSILETURRET,
#     MOTHERSHIP,
#     MULE,
#     MUTALISK,
#     NEXUS,
#     NYDUSCANAL,
#     NYDUSNETWORK,
#     OBSERVER,
#     OBSERVERSIEGEMODE,
#     ORACLE,
#     ORBITALCOMMAND,
#     ORBITALCOMMANDFLYING,
#     OVERLORD,
#     OVERLORDCOCOON,
#     OVERLORDTRANSPORT,
#     OVERSEER,
#     OVERSEERSIEGEMODE,
#     PARASITICBOMBDUMMY,
#     PHOENIX,
#     PHOTONCANNON,
#     PLANETARYFORTRESS,
#     POINTDEFENSEDRONE,
#     PROBE,
#     PYLON,
#     QUEEN,
#     QUEENBURROWED,
#     RAVAGER,
#     RAVAGERBURROWED,
#     RAVAGERCOCOON,
#     RAVEN,
#     REACTOR,
#     REAPER,
#     REFINERY,
#     ROACH,
#     ROACHBURROWED,
#     ROACHWARREN,
#     ROBOTICSBAY,
#     ROBOTICSFACILITY,
#     SCV,
#     SENSORTOWER,
#     SENTRY,
#     SHIELDBATTERY,
#     SIEGETANK,
#     SIEGETANKSIEGED,
#     SPAWNINGPOOL,
#     SPINECRAWLER,
#     SPINECRAWLERUPROOTED,
#     SPIRE,
#     SPORECRAWLER,
#     SPORECRAWLERUPROOTED,
#     STALKER,
#     STARGATE,
#     STARPORT,
#     STARPORTFLYING,
#     STARPORTREACTOR,
#     STARPORTTECHLAB,
#     SUPPLYDEPOT,
#     SUPPLYDEPOTLOWERED,
#     SWARMHOSTBURROWEDMP,
#     SWARMHOSTMP,
#     TECHLAB,
#     TEMPEST,
#     TEMPLARARCHIVE,
#     THOR,
#     THORAP,
#     TRANSPORTOVERLORDCOCOON,
#     TWILIGHTCOUNCIL,
#     ULTRALISK,
#     ULTRALISKBURROWED,
#     ULTRALISKCAVERN,
#     VIKINGASSAULT,
#     VIKINGFIGHTER,
#     VIPER,
#     VOIDRAY,
#     WARPGATE,
#     WARPPRISM,
#     WARPPRISMPHASING,
#     WIDOWMINE,
#     WIDOWMINEBURROWED,
#     ZEALOT,
#     ZERGLING,
#     ZERGLINGBURROWED,
# )
#
# units_created_by_ability_or_morph = OrderedDict(
#     {
#         # TERRAN
#         ## Abilities
#         ### Energy based
#         MULE: [ORBITALCOMMAND],
#         AUTOTURRET: [RAVEN],
#         ### Cost based
#         ORBITALCOMMAND: [BARRACKS],
#         PLANETARYFORTRESS: [ENGINEERINGBAY, REFINERY],
#         BARRACKSTECHLAB: [BARRACKS, REFINERY],
#         BARRACKSREACTOR: [BARRACKS, REFINERY],
#         FACTORYTECHLAB: [FACTORY],
#         FACTORYREACTOR: [FACTORY],
#         STARPORTTECHLAB: [STARPORT],
#         STARPORTREACTOR: [STARPORT],
#         ### Free
#         COMMANDCENTERFLYING: [COMMANDCENTER],
#         ORBITALCOMMANDFLYING: [ORBITALCOMMAND],
#         SUPPLYDEPOTLOWERED: [SUPPLYDEPOT],
#         BARRACKSFLYING: [BARRACKS],
#         FACTORYFLYING: [FACTORY],
#         STARPORTFLYING: [STARPORT],
#         WIDOWMINEBURROWED: [FACTORY],
#         SIEGETANKSIEGED: [FACTORYTECHLAB],
#         VIKINGASSAULT: [STARPORT],
#         LIBERATORAG: [STARPORT],
#         ## If not connected to a barracks/factory/starport, those addons become this
#         REACTOR: [BARRACKS],
#         TECHLAB: [BARRACKS],
#         # PROTOSS
#         ## Abilities
#         ### Cost based
#         INTERCEPTOR: [CARRIER],
#         ### Free
#         WARPGATE: [CYBERNETICSCORE],
#         ARCHON: [TWILIGHTCOUNCIL],
#         ADEPTPHASESHIFT: [ADEPT],
#         DISRUPTORPHASED: [DISRUPTOR],
#         OBSERVERSIEGEMODE: [ROBOTICSFACILITY],
#         WARPPRISMPHASING: [ROBOTICSFACILITY],
#         # ZERG
#         ## Abilities
#         ### Energy based
#         CREEPTUMORQUEEN: [CREEPTUMOR],
#         CHANGELING: [OVERSEER],
#         INFESTEDTERRANSEGG: [INFESTOR],
#         ### Cost based
#         LAIR: [SPAWNINGPOOL, EXTRACTOR],
#         HIVE: [INFESTATIONPIT],
#         GREATERSPIRE: [HIVE, SPIRE],
#         NYDUSCANAL: [NYDUSNETWORK],
#         RAVAGERCOCOON: [ROACH],
#         BANELINGCOCOON: [BANELINGNEST],
#         LURKERMPEGG: [LURKERDENMP],
#         BROODLORDCOCOON: [GREATERSPIRE, CORRUPTOR],
#         # One of these two is wrong:
#         OVERLORDCOCOON: [LAIR],
#         TRANSPORTOVERLORDCOCOON: [LAIR],
#         ### After cocoon
#         OVERLORDTRANSPORT: [LAIR],
#         OVERSEER: [LAIR],
#         LURKERMP: [LURKERDENMP],
#         BROODLORD: [GREATERSPIRE, CORRUPTOR],
#         BANELING: [BANELINGNEST],
#         RAVAGER: [ROACH],
#         CHANGELINGZEALOT: [OVERSEER],
#         CHANGELINGMARINE: [OVERSEER],
#         CHANGELINGMARINESHIELD: [OVERSEER],
#         CHANGELINGZERGLING: [OVERSEER],
#         CHANGELINGZERGLINGWINGS: [OVERSEER],
#         INFESTORTERRAN: [INFESTATIONPIT],
#         ### Free
#         OVERSEERSIEGEMODE: [LAIR],
#         LOCUSTMP: [SWARMHOSTMP],
#         LOCUSTMPFLYING: [SWARMHOSTMP],
#         BROODLING: [],
#         LARVA: [],
#         EGG: [],
#         CREEPTUMOR: [QUEEN],
#         CREEPTUMORBURROWED: [CREEPTUMOR],
#         SPINECRAWLERUPROOTED: [SPAWNINGPOOL],
#         SPORECRAWLERUPROOTED: [SPAWNINGPOOL],
#         ### Burrowed units
#         DRONEBURROWED: [DRONE],
#         ZERGLINGBURROWED: [SPAWNINGPOOL],
#         QUEENBURROWED: [QUEEN],
#         ROACHBURROWED: [ROACHWARREN],
#         RAVAGERBURROWED: [ROACH],
#         BANELINGBURROWED: [BANELINGNEST],
#         INFESTORBURROWED: [INFESTATIONPIT],
#         INFESTORTERRANBURROWED: [INFESTOR],
#         SWARMHOSTBURROWEDMP: [INFESTATIONPIT],
#         HYDRALISKBURROWED: [HYDRALISKDEN],
#         LURKERMPBURROWED: [LURKERDENMP],
#         ULTRALISKBURROWED: [ULTRALISKCAVERN],
#     }
# )
#
# buildings_created_by_worker = OrderedDict(
#     {
#         # TERRAN
#         ## Command card 1
#         COMMANDCENTER: [],
#         SUPPLYDEPOT: [],
#         REFINERY: [],
#         BARRACKS: [SUPPLYDEPOT],
#         ENGINEERINGBAY: [],
#         BUNKER: [BARRACKS],
#         MISSILETURRET: [ENGINEERINGBAY],
#         SENSORTOWER: [ENGINEERINGBAY, REFINERY],
#         ## Command card 2
#         GHOSTACADEMY: [BARRACKS],
#         FACTORY: [BARRACKS, REFINERY],
#         ARMORY: [FACTORY],
#         STARPORT: [FACTORY],
#         FUSIONCORE: [STARPORT],
#         # PROTOSS
#         ## Command card 1
#         NEXUS: [],
#         PYLON: [],
#         GATEWAY: [PYLON],
#         ASSIMILATOR: [],
#         FORGE: [PYLON],
#         PHOTONCANNON: [FORGE],
#         CYBERNETICSCORE: [GATEWAY],
#         SHIELDBATTERY: [CYBERNETICSCORE],
#         ## Command card 2
#         TWILIGHTCOUNCIL: [CYBERNETICSCORE, ASSIMILATOR],
#         STARGATE: [CYBERNETICSCORE, ASSIMILATOR],
#         ROBOTICSFACILITY: [CYBERNETICSCORE, ASSIMILATOR],
#         TEMPLARARCHIVE: [TWILIGHTCOUNCIL],
#         FLEETBEACON: [STARGATE],
#         ROBOTICSBAY: [ROBOTICSFACILITY],
#         DARKSHRINE: [TWILIGHTCOUNCIL],
#         # ZERG
#         ## Command card 1
#         HATCHERY: [],
#         EXTRACTOR: [],
#         SPAWNINGPOOL: [],
#         EVOLUTIONCHAMBER: [],
#         ROACHWARREN: [SPAWNINGPOOL, EXTRACTOR],
#         BANELINGNEST: [SPAWNINGPOOL, EXTRACTOR],
#         SPINECRAWLER: [SPAWNINGPOOL],
#         SPORECRAWLER: [SPAWNINGPOOL],
#         ## Command card 2
#         INFESTATIONPIT: [LAIR],
#         HYDRALISKDEN: [LAIR],
#         LURKERDENMP: [LAIR, HYDRALISKDEN],
#         SPIRE: [LAIR],
#         NYDUSNETWORK: [LAIR],
#         ULTRALISKCAVERN: [HIVE],
#     }
# )
#
# trainable_units = OrderedDict(
#     {
#         # TERRAN
#         # By townhall
#         SCV: [],
#         # By barracks
#         MARINE: [BARRACKS],
#         REAPER: [BARRACKS, REFINERY],
#         MARAUDER: [BARRACKSTECHLAB],
#         GHOST: [BARRACKSTECHLAB, GHOSTACADEMY],
#         # By factory
#         HELLION: [FACTORY],
#         # Can be produced directly from factory which imo has higher priority, than a morph from hellion
#         HELLIONTANK: [ARMORY],
#         WIDOWMINE: [FACTORY],
#         CYCLONE: [FACTORY],
#         SIEGETANK: [FACTORYTECHLAB],
#         THOR: [ARMORY, FACTORYTECHLAB],
#         # By starport
#         VIKINGFIGHTER: [STARPORT],
#         MEDIVAC: [STARPORT],
#         LIBERATOR: [STARPORT],
#         RAVEN: [STARPORTTECHLAB],
#         BANSHEE: [STARPORTTECHLAB],
#         BATTLECRUISER: [FUSIONCORE, STARPORTTECHLAB],
#         # PROTOSS
#         # By townhall
#         PROBE: [],
#         MOTHERSHIP: [FLEETBEACON],
#         # By gateway and warp gate
#         ZEALOT: [GATEWAY],
#         SENTRY: [CYBERNETICSCORE, ASSIMILATOR],
#         STALKER: [CYBERNETICSCORE, ASSIMILATOR],
#         ADEPT: [CYBERNETICSCORE, ASSIMILATOR],
#         HIGHTEMPLAR: [TEMPLARARCHIVE],
#         DARKTEMPLAR: [DARKSHRINE],
#         # By Stargate
#         PHOENIX: [STARGATE],
#         ORACLE: [STARGATE],
#         VOIDRAY: [STARGATE],
#         TEMPEST: [FLEETBEACON],
#         CARRIER: [FLEETBEACON],
#         # By Robo
#         OBSERVER: [ROBOTICSFACILITY],
#         WARPPRISM: [ROBOTICSFACILITY],
#         IMMORTAL: [ROBOTICSFACILITY],
#         COLOSSUS: [ROBOTICSBAY],
#         DISRUPTOR: [ROBOTICSBAY],
#         # ZERG
#         # By townhall
#         QUEEN: [SPAWNINGPOOL],
#         # By larva
#         DRONE: [],
#         OVERLORD: [],
#         ZERGLING: [SPAWNINGPOOL],
#         ROACH: [ROACHWARREN],
#         INFESTOR: [INFESTATIONPIT],
#         SWARMHOSTMP: [INFESTATIONPIT],
#         HYDRALISK: [HYDRALISKDEN],
#         MUTALISK: [SPIRE],
#         CORRUPTOR: [SPIRE],
#         VIPER: [HIVE],
#         ULTRALISK: [ULTRALISKCAVERN],
#     }
# )


class GenerateBot(sc2.BotAI):
    def __init__(self):
        # TODO: Missing are adept shade, disruptor shot, raven autoturret, and wrongly categorized are locust (swarmhost) and infested terran (infestor)

        # TODO: Some abilities are no longer in the game, or never made it into the game
        # UnitTypeId.PYLONOVERCHARGED is AbilityId.PURIFYMORPHPYLON_MOTHERSHIPCOREWEAPON
        # UnitTypeId.GUARDIANMP is AbilityId.MORPHTOGUARDIANMP_MORPHTOGUARDIANMP

        # List of all structures and their build ability
        self.structure_creation_ability_dict: Dict[UnitTypeId, AbilityId] = OrderedDict()
        # List of all units and their train ability (if they are trained from structure or larva)
        self.unit_train_ability_dict: Dict[UnitTypeId, AbilityId] = OrderedDict()
        # List of all units and their train ability (if they are trained from structure or larva)
        self.other_unit_creation_ability_dict: Dict[UnitTypeId, AbilityId] = OrderedDict()
        # List of all free morphs, like lifting a terran structure, burrowing a zerg unit or widow mine, or morphing observer/ovserseer into surveillance mode, or sieging a liberator or siege tank
        self.free_morph_abilities_dict: Dict[UnitTypeId, AbilityId] = OrderedDict()
        # Structure morphs that have a cost connected, like hatchery -> lair, commandcender -> OC/PF, spire -> greater spire
        self.structure_morph_abilities_dict: Dict[UnitTypeId, AbilityId] = OrderedDict()
        # Unit morphs with cost, e.g. baneling, lurker, ravager, broodlord
        self.unit_morph_abilities_dict: Dict[UnitTypeId, AbilityId] = OrderedDict()
        # Dict of all upgrades mapped to their exact research abilities
        self.upgrade_to_research_ability_dict: Dict[UpgradeId, AbilityId] = OrderedDict()

        # Dict of all the units abilities
        self.unit_type_abilities_dict: Dict[UnitTypeId, Set[AbilityId]] = OrderedDict()

        self.starter_units: Set[int] = None
        self.ability_query_units: Set[UnitTypeId] = None
        self.current_index = 0

        self.techlabs_created = False
        self.cheat_tech_researched = False

        self.waiting_for_unit_to_spawn: UnitTypeId = None
        self.waiting_tick = 0

    # HELPER FUNCTION

    def type_id_is_available(self, type_id: Union[UpgradeId, UnitTypeId]) -> bool:
        try:
            if isinstance(type_id, UpgradeId):
                upgrade_data = self._game_data.upgrades[type_id.value]
                creation_ability_data = upgrade_data.research_ability
                if not creation_ability_data._proto.remaps_to_ability_id:
                    return creation_ability_data._proto.available

                creation_ability_generic = AbilityId(creation_ability_data._proto.remaps_to_ability_id)
                generic_ability_data = self._game_data.abilities[creation_ability_generic.value]
                return generic_ability_data._proto.available

            if isinstance(type_id, UnitTypeId):
                unit_data = self._game_data.units[type_id.value]
                creation_ability_data = unit_data.creation_ability
                if not creation_ability_data._proto.remaps_to_ability_id:
                    return creation_ability_data._proto.available

                creation_ability_generic = AbilityId(creation_ability_data._proto.remaps_to_ability_id)
                generic_ability_data = self._game_data.abilities[creation_ability_generic.value]
                return generic_ability_data._proto.available
        except:
            pass
        return False

    def get_ability_data_from_unit_type(self, unit_type: UnitTypeId, get_generic=False):
        unit_data = self._game_data.units[unit_type.value]

        creation_ability_data = unit_data.creation_ability
        if creation_ability_data is None:
            return None

        if get_generic:
            if not creation_ability_data._proto.remaps_to_ability_id:
                return None
            creation_ability = AbilityId(creation_ability_data._proto.remaps_to_ability_id)
        else:
            creation_ability = AbilityId(creation_ability_data._proto.ability_id)
        # print(self._game_data.abilities[creation_ability.value]._proto)
        return creation_ability

    def get_ability_data_from_upgrade_type(self, upgrade_type: UpgradeId, get_generic=False):
        upgrade_data = self._game_data.upgrades[upgrade_type.value]

        creation_ability_data = upgrade_data.research_ability
        if creation_ability_data is None:
            return None

        if get_generic:
            if not creation_ability_data._proto.remaps_to_ability_id:
                return None
            creation_ability = AbilityId(creation_ability_data._proto.remaps_to_ability_id)
        else:
            creation_ability = AbilityId(creation_ability_data._proto.ability_id)
        # print(self._game_data.abilities[creation_ability.value]._proto)
        return creation_ability

    def get_generic_ability(self, ability: AbilityId) -> Optional[AbilityId]:
        """ Returns the generic ability. E.g. a barracks can build barrackstechlab, but the generic ability would be build techlab. Same for lift, land and burrow. """
        generic_ability_value = (
            self._game_data.abilities[ability.value]._proto.remaps_to_ability_id
            if ability.value in self._game_data.abilities
            else None
        )
        # Generic abilities are for example BUILD_REACTOR_STARPORT with just BUILD_REACTOR or LIFT_ORBITALCOMMAND can be just LIFT
        generic_ability = (
            AbilityId(generic_ability_value)
            if generic_ability_value is not None and generic_ability_value != 0
            else None
        )
        return generic_ability

    def get_creation_ability_from_unit_type(self):
        # CHECK ALL UNITS FOR THEIR CREATION ABILITY
        for unit_type_id in UnitTypeId:
            if not self.type_id_is_available(unit_type_id):
                continue
            unit_data = self._game_data.units[unit_type_id.value]
            creation_ability = self.get_ability_data_from_unit_type(unit_type_id)
            creation_ability_data = self._game_data.abilities[creation_ability.value]
            creation_ability_generic = self.get_ability_data_from_unit_type(unit_type_id, get_generic=True)
            is_building: bool = creation_ability_data._proto.is_building
            # https://github.com/Blizzard/s2client-proto/blob/9906df71d6909511907d8419b33acc1a3bd51ec0/s2clientprotocol/data.proto#L21
            # Target.None Target.Point Target.Unit Target.PointOrUnit Target.PointOrNone
            target: Target = creation_ability_data._proto.target
            allow_minimap: bool = creation_ability_data._proto.allow_minimap
            has_cost = unit_data._proto.mineral_cost > 0 or unit_data._proto.vespene_cost > 0
            has_build_time = unit_data._proto.build_time > 0
            is_free_unit_morph: bool = unit_data._proto.unit_alias and unit_data._proto.unit_id != unit_data._proto.unit_alias
            unit_has_tech_alias: bool = bool(unit_data._proto.tech_alias)
            is_unknown: bool = unit_data._proto.armor > 9 or unit_data._proto.race == Race.NoRace.value

            # Is building because of the is building property and has target, or gas building because it targets a unit
            if is_building and has_build_time:
                print(
                    f"Structure creation ability of {unit_type_id} is {creation_ability if creation_ability_generic is None else creation_ability_generic}"
                )
                self.structure_creation_ability_dict[unit_type_id] = (
                    creation_ability if creation_ability_generic is None else creation_ability_generic
                )

            # Is morph ability because it has a unit alias, these morphs should be free of cost
            elif is_free_unit_morph:  # Target.None.value
                print(
                    f"Free unit ability of {unit_type_id} is {creation_ability if creation_ability_generic is None else creation_ability_generic}"
                )
                self.free_morph_abilities_dict[unit_type_id] = (
                    creation_ability if creation_ability_generic is None else creation_ability_generic
                )

            # Morphing structures like spire, hatch, command center can morph into greater spire, lair, OC/PF
            elif unit_has_tech_alias:  # Target.Point.value
                print(
                    f"Structure costly morph ability of {unit_type_id} is {creation_ability if creation_ability_generic is None else creation_ability_generic}"
                )
                self.structure_morph_abilities_dict[unit_type_id] = (
                    creation_ability if creation_ability_generic is None else creation_ability_generic
                )

            # Any other morph ability, usually ling morphing into banes, roach morphing into ravager etc.
            elif "MORPH" in str(creation_ability):  # Target.Point.value
                print(
                    f"Unit costly morph ability of {unit_type_id} is {creation_ability if creation_ability_generic is None else creation_ability_generic}"
                )
                self.unit_morph_abilities_dict[unit_type_id] = (
                    creation_ability if creation_ability_generic is None else creation_ability_generic
                )

            # Is unit train ability because it has cost and target type is None
            elif has_cost and target == 1:
                print(
                    f"Unit train creation ability of {unit_type_id} is {creation_ability if creation_ability_generic is None else creation_ability_generic}"
                )
                self.unit_train_ability_dict[unit_type_id] = (
                    creation_ability if creation_ability_generic is None else creation_ability_generic
                )

            elif is_unknown:
                pass

            else:
                print(
                    f"Other creation ability of {unit_type_id} is {creation_ability if creation_ability_generic is None else creation_ability_generic}, unit info is \n{unit_data._proto} and ability data is \n{creation_ability_data._proto}"
                )
                self.other_unit_creation_ability_dict[unit_type_id] = (
                    creation_ability if creation_ability_generic is None else creation_ability_generic
                )

    def get_creation_research_ability_from_upgrade_type(self):
        # CHECK ALL UPGRADES FOR THEIR CREATION ABILITY
        for upgrade_id in UpgradeId:
            if not self.type_id_is_available(upgrade_id):
                continue

            research_ability = self.get_ability_data_from_upgrade_type(upgrade_id)
            # Research ability doesn't exist
            if research_ability is None:
                continue
            generic_research_ability = self.get_ability_data_from_upgrade_type(upgrade_id, get_generic=True)

            print(
                f"Research ability of upgrade {upgrade_id} is {research_ability} and generic research is {generic_research_ability}"
            )
            # Set research ability to upgrade id
            self.upgrade_to_research_ability_dict[upgrade_id] = research_ability

    def get_starting_units(self):
        self.starter_units = (self.units | self.structures).tags
        self.ability_query_units: List[UnitTypeId] = list(
            set.union(
                *[
                    set(x)
                    for x in [
                        self.structure_creation_ability_dict,
                        self.unit_train_ability_dict,
                        self.free_morph_abilities_dict,
                        self.structure_morph_abilities_dict,
                        self.unit_morph_abilities_dict,
                    ]
                ]
            )
        )

        print(f"Querying abilities of the following unit types: {self.ability_query_units}")

    def is_structure(self, unit_type: UnitTypeId):
        unit_data = self._game_data.units[unit_type.value]
        return Attribute.Structure.value in unit_data.attributes

    async def set_cheats(self, turn_on=True):
        if self.cheat_tech_researched != turn_on:
            # Enable tech
            self.cheat_tech_researched = True
            await self._client.debug_tech_tree()
        elif self.cheat_tech_researched != turn_on:
            # Disable tech
            self.cheat_tech_researched = False
            await self._client.debug_tech_tree()

    async def create_techlabs(self):
        height, width = self.game_info.placement_grid.data_numpy.shape
        offsets_y = [0, 3, 6]
        offset_land_position = Point2((-2.5, 0.5))
        for x in range(width):
            for y in range(height):
                # can_place = True
                positions = [Point2((x + a, y + b)) for a in [0, 3] for b in [0, 3, 6]]
                barracks_ability_data = self._game_data.abilities[AbilityId.TERRANBUILD_BARRACKS.value]
                results = await self._client.query_building_placement(
                    barracks_ability_data, positions, ignore_resources=True
                )
                can_place = len([True for a in results if a == ActionResult.Success]) == 6
                if can_place:
                    await self._client.debug_create_unit(
                        [
                            [UnitTypeId.BARRACKS, 1, Point2((x, y)), 1],
                            [UnitTypeId.BARRACKSTECHLAB, 1, Point2((x, y)) - offset_land_position, 1],
                            [UnitTypeId.FACTORY, 1, Point2((x, y + 3)), 1],
                            [UnitTypeId.FACTORYTECHLAB, 1, Point2((x, y + 3)) - offset_land_position, 1],
                            [UnitTypeId.STARPORT, 1, Point2((x, y + 6)), 1],
                            [UnitTypeId.STARPORTTECHLAB, 1, Point2((x, y + 6)) - offset_land_position, 1],
                        ]
                    )
                    print(f"Spawning structures and techlabs")
                    return True
        return False

    async def spawn_requirement_structures(self):
        # It is required to spawn support structure for some buildings like:
        # To research roach speed, bane speed: lair or hive is required
        # To research smart servos for terran, armory is required
        # To research liberator range in starport techlab, fusion core is required
        # To research +2 +3 infantry weapons in engi bay, armory is required
        # To research +2 +3 in cyber core, fleet beacon is required
        # To research +2 +3 in forge, twilight council is required
        # To research +2 +3 in spire, greater spire is required
        # To research lurker den speed burrow upgrade, hive is required
        # For gateway and warpgate to train all units, building requirement is needed
        # To morph to lair, spawning pool is needed
        # To spawn to hive, infestation pit is needed
        support_structures = [
            UnitTypeId.ARMORY,
            UnitTypeId.FUSIONCORE,
            UnitTypeId.LAIR,
            UnitTypeId.HIVE,
            UnitTypeId.TWILIGHTCOUNCIL,
            UnitTypeId.FLEETBEACON,
            UnitTypeId.GREATERSPIRE,
            UnitTypeId.TEMPLARARCHIVE,
            UnitTypeId.DARKSHRINE,
            UnitTypeId.CYBERNETICSCORE,
            UnitTypeId.SPAWNINGPOOL,
            UnitTypeId.INFESTATIONPIT,
        ]
        spawn_center = self.structures.center
        await self._client.debug_create_unit([[unit_type, 1, spawn_center, 1] for unit_type in support_structures])

    def dump_dict_to_file(
        self, my_dict: dict, file_path: str, dict_name: str, file_header: str = "", dict_type_annotation: str = ""
    ):
        tab = 4 * " "
        with open(file_path, "w") as f:
            f.write(file_header)
            f.write("\n")
            f.write(f"{dict_name}{dict_type_annotation} = " + "{\n")
            for key, value in my_dict.items():
                if isinstance(value, (set, list)):
                    value_str = "{" + ", ".join(str(i) for i in value) + "}"
                else:
                    value_str = str(value)
                line = f"{tab}{str(key)}: {value_str},\n"
                f.write(line)
            f.write("}")

        # Apply formatting if file is too long
        subprocess.run(["black", file_path])

    def dump_data_to_files(self):
        path = os.path.dirname(__file__)
        dicts_path = os.path.join(path, "sc2", "dicts")
        os.makedirs(dicts_path, exist_ok=True)

        structure_creation_dict_path = os.path.join(dicts_path, "structure_creation.py")
        unit_train_dict_path = os.path.join(dicts_path, "unit_train.py")
        free_morphs_dict_path = os.path.join(dicts_path, "free_morphs.py")
        structure_morphs_dict_path = os.path.join(dicts_path, "structure_morphs.py")
        unit_morphs_dict_path = os.path.join(dicts_path, "unit_morphs.py")
        upgrade_research_dict_path = os.path.join(dicts_path, "upgrade_research.py")
        unit_abilities_dict_path = os.path.join(dicts_path, "unit_abilities.py")

        file_header = """
# THIS FILE WAS AUTOMATICALLY GENERATED BY generate_conversion_dicts_bot.py DO NOT CHANGE MANUALLY!
# ANY CHANGE WILL BE OVERWRITTEN

from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
# from sc2.ids.buff_id import BuffId
from sc2.ids.upgrade_id import UpgradeId
# from sc2.ids.effect_id import EffectId

from typing import Dict, Set#, List, Tuple, Union, Optional
        """

        self.dump_dict_to_file(
            self.structure_creation_ability_dict,
            structure_creation_dict_path,
            dict_name="STRUCTURE_CREATION",
            file_header=file_header,
            dict_type_annotation=": Dict[UnitTypeId, AbilityId]",
        )
        self.dump_dict_to_file(
            self.unit_train_ability_dict,
            unit_train_dict_path,
            dict_name="UNIT_TRAIN",
            file_header=file_header,
            dict_type_annotation=": Dict[UnitTypeId, AbilityId]",
        )
        self.dump_dict_to_file(
            self.free_morph_abilities_dict,
            free_morphs_dict_path,
            dict_name="FREE_MORPH",
            file_header=file_header,
            dict_type_annotation=": Dict[UnitTypeId, AbilityId]",
        )
        self.dump_dict_to_file(
            self.structure_morph_abilities_dict,
            structure_morphs_dict_path,
            dict_name="STRUCTURE_MORPH",
            file_header=file_header,
            dict_type_annotation=": Dict[UnitTypeId, AbilityId]",
        )
        self.dump_dict_to_file(
            self.unit_morph_abilities_dict,
            unit_morphs_dict_path,
            dict_name="UNIT_MORPH",
            file_header=file_header,
            dict_type_annotation=": Dict[UnitTypeId, AbilityId]",
        )
        self.dump_dict_to_file(
            self.upgrade_to_research_ability_dict,
            upgrade_research_dict_path,
            dict_name="UPGRADE_ABILITY",
            file_header=file_header,
            dict_type_annotation=": Dict[UpgradeId, AbilityId]",
        )
        self.dump_dict_to_file(
            self.unit_type_abilities_dict,
            unit_abilities_dict_path,
            dict_name="UNIT_ABILITIES",
            file_header=file_header,
            dict_type_annotation=": Dict[UnitTypeId, Set[AbilityId]]",
        )

    async def on_start(self):
        self.game_step = 4
        await self.set_cheats()
        self.get_creation_ability_from_unit_type()
        self.get_creation_research_ability_from_upgrade_type()
        await self.spawn_requirement_structures()

    async def on_step(self, iteration: int):
        if iteration < 2:
            return
        if iteration == 2:
            self.get_starting_units()

        # CREATE ALL STRUCTURES AND UNITS
        map_center = self.game_info.map_center
        if not self.techlabs_created:
            if self.waiting_for_unit_to_spawn is None:
                for index, unit_id in enumerate(self.ability_query_units):
                    # Enable tech, for example banshee and battlecruiser need cloak or yamato researched for the ability to show up
                    if self.is_structure(unit_id):
                        await self.set_cheats(turn_on=False)
                    else:
                        # Disable tech so that upgrades appear in the structures again
                        await self.set_cheats(turn_on=True)

                    if index == self.current_index:
                        # Protoss structures need to be powered to have their abilities listed, so spawn a pylon with them
                        await self._client.debug_create_unit(
                            [[UnitTypeId.PYLON, 1, map_center, 1], [unit_id, 1, map_center, 1]]
                        )
                        self.current_index += 1
                        self.waiting_for_unit_to_spawn = unit_id
                        return

            # IN THE FOLLOWING FRAME, QUERY THEIR ABILITIES, THEN DESTROY THEM
            else:
                newly_spawned_units: Units = (self.units | self.structures).filter(
                    lambda u: u.tag not in self.starter_units
                )
                target_unit_type_units = (self.units | self.structures).filter(
                    lambda u: u.tag not in self.starter_units and u.type_id == self.waiting_for_unit_to_spawn
                )
                if not target_unit_type_units:
                    # Wanted unit type has not spawned yet
                    self.waiting_tick += 1
                    if self.waiting_tick >= 5:
                        print(f"Waited 5 frames for unit type {self.waiting_for_unit_to_spawn} to spawn, but it didn't")
                        self.waiting_for_unit_to_spawn = None
                    return
                if target_unit_type_units:
                    target_unit_type_unit: Unit = target_unit_type_units[0]
                    abilities = await self.get_available_abilities(
                        [target_unit_type_unit], ignore_resource_requirements=True
                    )
                    abilities_unit_type = abilities[0]
                    self.unit_type_abilities_dict[target_unit_type_unit.type_id] = abilities_unit_type
                    print(f"Abilities of unit type {target_unit_type_unit.type_id} are {abilities_unit_type}")
                await self._client.debug_kill_unit(newly_spawned_units)
                self.waiting_for_unit_to_spawn = None
                self.waiting_tick = 0
                return

        # Create techlabs with barracks, factory and starport attached
        if not self.techlabs_created:
            self.techlabs_created = await self.create_techlabs()
            # Disable tech so that upgrades appear in the structures again
            await self.set_cheats(turn_on=False)
            return
        else:
            terran_production_types = [UnitTypeId.BARRACKS, UnitTypeId.FACTORY, UnitTypeId.STARPORT]
            techlab_types = [UnitTypeId.BARRACKSTECHLAB, UnitTypeId.FACTORYTECHLAB, UnitTypeId.STARPORTTECHLAB]
            for techlab_type in techlab_types:
                techlabs: Units = self.structures.of_type(techlab_type)
                techlab_abilities = await self.get_available_abilities(techlabs, ignore_resource_requirements=True)
                self.unit_type_abilities_dict[techlab_type] = techlab_abilities[0]
                print(f"Techlab abilities of type {techlab_type} are: {techlab_abilities[0]}")
            # Clean up
            await self._client.debug_kill_unit(
                self.structures.filter(lambda u: u.type_id in (techlab_types + terran_production_types))
            )

        self.dump_data_to_files()
        await self._client.leave()


def main():
    sc2.run_game(
        sc2.maps.get("(2)CatalystLE"),
        [Bot(Race.Terran, GenerateBot()), Computer(Race.Zerg, Difficulty.Easy)],
        realtime=False,
    )


if __name__ == "__main__":
    main()
