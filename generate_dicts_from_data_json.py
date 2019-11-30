import json, os, subprocess
import lzma, pickle
from typing import Dict, Set, List, Union, Optional

from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.effect_id import EffectId
from sc2.game_data import GameData

from collections import OrderedDict

# from ordered_set import OrderedSet

"""
Script requirements:
pip install black

This script does the following:

- Loop over all abilities, checking what unit they create and if it requires a placement position
- Loop over all units, checking what abilities they have and which of those create units, and what tech requirements they have
- Loop over all all upgrades and get their creation ability, which unit can research it and what building requirements there are
- Loop over all units and get their unit and tech aliases

Dentosals data.json
https://github.com/BurnySc2/sc2-techtree/tree/develop/data

json viewers to inspect the data.json manually:
http://jsonviewer.stack.hu/
https://jsonformatter.org/json-viewer
"""

# Custom repr function so that the output is always the same and only changes when there were changes in the data.json tech tree file
# The output just needs to be ordered (sorted by enum name), but it does not matter anymore if the bot then imports an unordered dict and set
class OrderedDict2(OrderedDict):
    def __repr__(self):
        if not self:
            return "{}"
        return (
            "{"
            + ", ".join(f"{repr(key)}: {repr(value)}" for key, value in sorted(self.items(), key=lambda u: u[0].name))
            + "}"
        )


class OrderedSet2(set):
    def __repr__(self):
        if not self:
            return "set()"
        return "{" + ", ".join(repr(item) for item in sorted(self, key=lambda u: u.name)) + "}"


def dump_dict_to_file(
    my_dict: OrderedDict2, file_path: str, dict_name: str, file_header: str = "", dict_type_annotation: str = ""
):
    with open(file_path, "w") as f:
        f.write(file_header)
        f.write("\n")
        f.write(f"{dict_name}{dict_type_annotation} = ")
        assert isinstance(my_dict, OrderedDict2)
        print(my_dict)
        f.write(repr(my_dict))

    # Apply formatting
    subprocess.run(["black", file_path])


def generate_init_file(dict_file_paths: List[str], file_path: str, file_header: str):
    base_file_names = sorted(os.path.splitext(os.path.basename(path))[0] for path in dict_file_paths)

    with open(file_path, "w") as f:
        f.write(file_header)
        f.write("\n")

        all_line = f"__all__ = {base_file_names}"
        print(all_line)
        f.write(all_line)

    # Apply formatting
    subprocess.run(["black", file_path])


def get_unit_train_build_abilities(data):
    ability_data = data["Ability"]
    unit_data = data["Unit"]
    upgrade_data = data["Upgrade"]

    # From which abilities can a unit be trained
    train_abilities: Dict[UnitTypeId, Set[AbilityId]] = OrderedDict2()
    # If the ability requires a placement position
    ability_requires_placement: Set[AbilityId] = set()
    # Map ability to unittypeid
    ability_to_unittypeid_dict: Dict[AbilityId, UnitTypeId] = OrderedDict2()

    # From which abilities can a unit be morphed
    # unit_morph_abilities: Dict[UnitTypeId, Set[AbilityId]] = {}

    entry: dict
    for entry in ability_data:
        """
        "target": "PointOrUnit"
        """
        if isinstance(entry.get("target", {}), str):
            continue
        ability_id: AbilityId = AbilityId(entry["id"])
        created_unit_type_id: UnitTypeId

        # Check if it is a unit train ability
        requires_placement = False
        train_unit_type_id_value: int = entry.get("target", {}).get("Train", {}).get("produces", 0)
        train_place_unit_type_id_value: int = entry.get("target", {}).get("TrainPlace", {}).get("produces", 0)
        morph_unit_type_id_value: int = entry.get("target", {}).get("Morph", {}).get("produces", 0)
        build_unit_type_id_value: int = entry.get("target", {}).get("Build", {}).get("produces", 0)
        build_on_unit_unit_type_id_value: int = entry.get("target", {}).get("BuildOnUnit", {}).get("produces", 0)

        if not train_unit_type_id_value and train_place_unit_type_id_value:
            train_unit_type_id_value = train_place_unit_type_id_value
            requires_placement = True

        # Collect larva morph abilities, and one way morphs (exclude burrow, hellbat morph, siege tank siege)
        # Also doesnt include building addons
        if not train_unit_type_id_value and (
            "LARVATRAIN_" in ability_id.name
            or ability_id
            in {
                AbilityId.MORPHTOBROODLORD_BROODLORD,
                AbilityId.MORPHZERGLINGTOBANELING_BANELING,
                AbilityId.MORPHTORAVAGER_RAVAGER,
                AbilityId.MORPH_LURKER,
                AbilityId.UPGRADETOLAIR_LAIR,
                AbilityId.UPGRADETOHIVE_HIVE,
                AbilityId.UPGRADETOGREATERSPIRE_GREATERSPIRE,
                AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND,
                AbilityId.UPGRADETOPLANETARYFORTRESS_PLANETARYFORTRESS,
                AbilityId.MORPH_OVERLORDTRANSPORT,
                AbilityId.MORPH_OVERSEER,
            }
        ):
            # If all morph units are used, unit_trained_from.py will be "wrong" because it will list that a siege tank can be trained from siegetanksieged and similar:
            # UnitTypeId.SIEGETANK: {UnitTypeId.SIEGETANKSIEGED, UnitTypeId.FACTORY},
            # if not train_unit_type_id_value and morph_unit_type_id_value:
            train_unit_type_id_value = morph_unit_type_id_value

        # Add all build abilities, like construct buildings and train queen (exception)
        if not train_unit_type_id_value and build_unit_type_id_value:
            train_unit_type_id_value = build_unit_type_id_value
            if "BUILD_" in entry["name"]:
                requires_placement = True

        # Add build gas building (refinery, assimilator, extractor)
        # TODO: target needs to be a unit, not a position, but i dont want to store an extra line just for this - needs to be an exception in bot_ai.py
        if not train_unit_type_id_value and build_on_unit_unit_type_id_value:
            train_unit_type_id_value = build_on_unit_unit_type_id_value

        if train_unit_type_id_value:
            created_unit_type_id = UnitTypeId(train_unit_type_id_value)

            if created_unit_type_id not in train_abilities:
                train_abilities[created_unit_type_id] = {ability_id}
            else:
                train_abilities[created_unit_type_id].add(ability_id)
            if requires_placement:
                ability_requires_placement.add(ability_id)

            ability_to_unittypeid_dict[ability_id] = created_unit_type_id

    """
    unit_train_abilities = {
        UnitTypeId.GATEWAY: {
            UnitTypeId.ADEPT: {
                "ability": AbilityId.TRAIN_ADEPT,
                "requires_techlab": False,
                "required_building": UnitTypeId.CYBERNETICSCORE, # Or None
                "requires_placement_position": False, # True for warp gate
                "requires_power": True, # If a pylon nearby is required
            },
            UnitTypeId.Zealot: {
                "ability": AbilityId.GATEWAYTRAIN_ZEALOT,
                ...
            }
        }
    }
    """
    unit_train_abilities: Dict[UnitTypeId, Dict[str, Union[AbilityId, bool, UnitTypeId]]] = OrderedDict2()
    for entry in unit_data:
        unit_abilities = entry.get("abilities", [])
        unit_type = UnitTypeId(entry["id"])
        current_unit_train_abilities = OrderedDict2()
        for ability_info in unit_abilities:
            ability_id_value: int = ability_info.get("ability", 0)
            if ability_id_value:
                ability_id: AbilityId = AbilityId(ability_id_value)
                # Ability is not a train ability
                if ability_id not in ability_to_unittypeid_dict:
                    continue

                requires_techlab: bool = False
                required_building: Optional[UnitTypeId] = None
                requires_placement_position: bool = False
                requires_power: bool = False

                """
                requirements = [
                    {
                        "addon": 5
                    },
                    {
                        "building": 29
                    }
                  ]
                """
                requirements: List[Dict[str, int]] = ability_info.get("requirements", [])
                if requirements:
                    # Assume train abilities only have one tech building requirement; thors requiring armory and techlab is seperatedly counted
                    assert (
                        len([req for req in requirements if req.get("building", 0)]) <= 1
                    ), f"Error: Building {unit_type} has more than one tech requirements with train ability {ability_id}"
                    # UnitTypeId 5 == Techlab
                    requires_techlab: bool = any(req for req in requirements if req.get("addon", 0) == 5)
                    requires_tech_builing_id_value: int = next(
                        (req["building"] for req in requirements if req.get("building", 0)), 0
                    )
                    if requires_tech_builing_id_value:
                        required_building = UnitTypeId(requires_tech_builing_id_value)

                if ability_id in ability_requires_placement:
                    requires_placement_position = True

                requires_power = entry.get("needs_power", False)

                resulting_unit = ability_to_unittypeid_dict[ability_id]

                ability_dict = {"ability": ability_id}
                # Only add boolean values and tech requirement if they actually exist, to make the resulting dict file smaller
                if requires_techlab:
                    ability_dict["requires_techlab"] = requires_techlab
                if required_building:
                    ability_dict["required_building"] = required_building
                if requires_placement_position:
                    ability_dict["requires_placement_position"] = requires_placement_position
                if requires_power:
                    ability_dict["requires_power"] = requires_power
                current_unit_train_abilities[resulting_unit] = ability_dict

        if current_unit_train_abilities:
            unit_train_abilities[unit_type] = current_unit_train_abilities

    return unit_train_abilities


def get_upgrade_abilities(data):
    ability_data = data["Ability"]
    unit_data = data["Unit"]
    upgrade_data = data["Upgrade"]

    ability_to_upgrade_dict: Dict[AbilityId, UpgradeId] = OrderedDict2()

    """
    We want to be able to research an upgrade by doing
    await self.can_research(UpgradeId, return_idle_structures=True) -> returns list of idle structures that can research it
    So we need to assign each upgrade id one building type, and its research ability and requirements (e.g. armory for infantry level 2)
    """

    # Collect all upgrades and their corresponding abilities
    entry: dict
    for entry in ability_data:
        if isinstance(entry.get("target", {}), str):
            continue
        ability_id: AbilityId = AbilityId(entry["id"])
        researched_ability_id: UnitTypeId

        upgrade_id_value: int = entry.get("target", {}).get("Research", {}).get("upgrade", 0)
        if upgrade_id_value:
            upgrade_id: UpgradeId = UpgradeId(upgrade_id_value)

            ability_to_upgrade_dict[ability_id] = upgrade_id

    """
    unit_research_abilities = {
        UnitTypeId.ENGINEERINGBAY: {
            UpgradeId.TERRANINFANTRYWEAPONSLEVEL1:
            {
                "ability": AbilityId.ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL1,
                "required_building": None,
                "requires_power": False, # If a pylon nearby is required
            },
            UpgradeId.TERRANINFANTRYWEAPONSLEVEL2: {
                "ability": AbilityId.ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL2,
                "required_building": UnitTypeId.ARMORY,
                "requires_power": False, # If a pylon nearby is required
            },
        }
    }
    """
    unit_research_abilities = OrderedDict2()
    for entry in unit_data:
        unit_abilities = entry.get("abilities", [])
        unit_type = UnitTypeId(entry["id"])

        if unit_type == UnitTypeId.TECHLAB:
            continue

        current_unit_research_abilities = OrderedDict2()
        for ability_info in unit_abilities:
            ability_id_value: int = ability_info.get("ability", 0)
            if ability_id_value:
                ability_id: AbilityId = AbilityId(ability_id_value)
                # Upgrade is not a known upgrade ability
                if ability_id not in ability_to_upgrade_dict:
                    continue

                required_building = None
                requirements = ability_info.get("requirements", [])
                if requirements:
                    req_building_id_value = next(
                        (req["building"] for req in requirements if req.get("building", 0)), None
                    )
                    if req_building_id_value:
                        req_building_id = UnitTypeId(req_building_id_value)
                        required_building = req_building_id

                requires_power = entry.get("needs_power", False)

                resulting_upgrade = ability_to_upgrade_dict[ability_id]

                research_info = {"ability": ability_id}
                if required_building:
                    research_info["required_building"] = required_building
                if requires_power:
                    research_info["requires_power"] = requires_power
                current_unit_research_abilities[resulting_upgrade] = research_info

        if current_unit_research_abilities:
            unit_research_abilities[unit_type] = current_unit_research_abilities

    return unit_research_abilities


def get_unit_created_from(unit_train_abilities: dict):
    unit_created_from = OrderedDict2()

    for creator_unit, create_abilities in unit_train_abilities.items():
        for created_unit, create_info in create_abilities.items():
            if created_unit not in unit_created_from:
                unit_created_from[created_unit] = OrderedSet2()
            unit_created_from[created_unit].add(creator_unit)

    return unit_created_from


def get_upgrade_researched_from(unit_research_abilities: dict):
    upgrade_researched_from = OrderedDict2()

    for researcher_unit, research_abilities in unit_research_abilities.items():
        for upgrade, research_info in research_abilities.items():
            upgrade_researched_from[upgrade] = researcher_unit

    return upgrade_researched_from


def get_unit_abilities(data: dict):
    ability_data = data["Ability"]
    unit_data = data["Unit"]
    upgrade_data = data["Upgrade"]

    all_unit_abilities: Dict[UnitTypeId, Set[AbilityId]] = OrderedDict2()
    entry: dict
    for entry in unit_data:
        entry_unit_abilities = entry.get("abilities", [])
        unit_type = UnitTypeId(entry["id"])
        current_collected_unit_abilities: Set[AbilityId] = OrderedSet2()
        for ability_info in entry_unit_abilities:
            ability_id_value: int = ability_info.get("ability", 0)
            if ability_id_value:
                ability_id: AbilityId = AbilityId(ability_id_value)
                current_collected_unit_abilities.add(ability_id)

        # print(unit_type, current_unit_abilities)
        if current_collected_unit_abilities:
            all_unit_abilities[unit_type] = current_collected_unit_abilities
    return all_unit_abilities


def generate_unit_alias_dict(data: dict):
    ability_data = data["Ability"]
    unit_data = data["Unit"]
    upgrade_data = data["Upgrade"]

    # Load pickled game data files from one of the test files
    path = os.path.dirname(__file__)
    pickled_files_folder_path = os.path.join(path, "test", "pickle_data")
    pickled_files = os.listdir(pickled_files_folder_path)
    random_pickled_file = next(f for f in pickled_files if f.endswith(".xz"))
    with lzma.open(os.path.join(pickled_files_folder_path, random_pickled_file), "rb") as f:
        raw_game_data, raw_game_info, raw_observation = pickle.load(f)
        game_data = GameData(raw_game_data.data)

    all_unit_aliases: Dict[UnitTypeId, UnitTypeId] = OrderedDict2()
    all_tech_aliases: Dict[UnitTypeId, Set[UnitTypeId]] = OrderedDict2()

    entry: dict
    for entry in unit_data:
        unit_type_value = entry["id"]
        unit_type = UnitTypeId(entry["id"])

        current_unit_tech_aliases: Set[UnitTypeId] = OrderedSet2()

        assert unit_type_value in game_data.units, f"Unit {unit_type} not listed in game_data.units"
        unit_alias: int = game_data.units[unit_type_value]._proto.unit_alias
        if unit_alias:
            # Might be 0 if it has no alias
            unit_alias_unit_type_id = UnitTypeId(unit_alias)
            all_unit_aliases[unit_type] = unit_alias_unit_type_id

        tech_aliases: List[int] = game_data.units[unit_type_value]._proto.tech_alias

        for tech_alias in tech_aliases:
            # Might be 0 if it has no alias
            unit_alias_unit_type_id = UnitTypeId(tech_alias)
            current_unit_tech_aliases.add(unit_alias_unit_type_id)

        if current_unit_tech_aliases:
            all_tech_aliases[unit_type] = current_unit_tech_aliases

    return all_unit_aliases, all_tech_aliases


def generate_redirect_abilities_dict(data: dict):
    ability_data = data["Ability"]
    unit_data = data["Unit"]
    upgrade_data = data["Upgrade"]

    # Load pickled game data files
    path = os.path.dirname(__file__)
    pickled_files_folder_path = os.path.join(path, "test", "pickle_data")
    pickled_files = os.listdir(pickled_files_folder_path)
    random_pickled_file = next(f for f in pickled_files if f.endswith(".xz"))
    with lzma.open(os.path.join(pickled_files_folder_path, random_pickled_file), "rb") as f:
        raw_game_data, raw_game_info, raw_observation = pickle.load(f)
        game_data = GameData(raw_game_data.data)

    all_redirect_abilities: Dict[AbilityId, AbilityId] = OrderedDict2()

    entry: dict
    for entry in ability_data:
        ability_id_value: int = entry["id"]
        try:
            ability_id: AbilityId = AbilityId(ability_id_value)
        except Exception as e:
            print(f"Error with ability id value {ability_id_value}")
            continue

        generic_redirect_ability_value: int = game_data.abilities[ability_id_value]._proto.remaps_to_ability_id
        if generic_redirect_ability_value:
            # Might be 0 if it has no redirect ability
            all_redirect_abilities[ability_id] = AbilityId(generic_redirect_ability_value)

    return all_redirect_abilities


def main():
    path = os.path.dirname(__file__)

    data_path = os.path.join(path, "data", "data.json")
    with open(data_path) as f:
        data = json.load(f)

    dicts_path = os.path.join(path, "sc2", "dicts")
    os.makedirs(dicts_path, exist_ok=True)

    # All unit train and build abilities
    unit_train_abilities = get_unit_train_build_abilities(data=data)
    unit_creation_dict_path = os.path.join(dicts_path, "unit_train_build_abilities.py")

    # All upgrades and which building can research which upgrade
    unit_research_abilities = get_upgrade_abilities(data=data)
    unit_research_abilities_dict_path = os.path.join(dicts_path, "unit_research_abilities.py")

    # All train abilities (where a unit can be trained from)
    unit_trained_from = get_unit_created_from(unit_train_abilities=unit_train_abilities)
    unit_trained_from_dict_path = os.path.join(dicts_path, "unit_trained_from.py")

    # All research abilities (where an upgrade can be researched from)
    upgrade_researched_from = get_upgrade_researched_from(unit_research_abilities=unit_research_abilities)
    upgrade_researched_from_dict_path = os.path.join(dicts_path, "upgrade_researched_from.py")

    # All unit abilities without requirements
    unit_abilities = get_unit_abilities(data=data)
    unit_abilities_dict_path = os.path.join(dicts_path, "unit_abilities.py")

    # All unit_alias and tech_alias of a unit type
    unit_unit_alias, unit_tech_alias = generate_unit_alias_dict(data=data)
    unit_unit_alias_dict_path = os.path.join(dicts_path, "unit_unit_alias.py")
    unit_tech_alias_dict_path = os.path.join(dicts_path, "unit_tech_alias.py")

    # All redirect (generic) abilities of abilities
    all_redirect_abilities = generate_redirect_abilities_dict(data=data)
    all_redirect_abilities_path = os.path.join(dicts_path, "generic_redirect_abilities.py")

    file_name = os.path.basename(__file__)
    file_header = f"""
# THIS FILE WAS AUTOMATICALLY GENERATED BY "{file_name}" DO NOT CHANGE MANUALLY!
# ANY CHANGE WILL BE OVERWRITTEN

from ..ids.unit_typeid import UnitTypeId
from ..ids.ability_id import AbilityId
from ..ids.upgrade_id import UpgradeId
# from ..ids.buff_id import BuffId
# from ..ids.effect_id import EffectId

from typing import Dict, Set, Union
    """

    dict_file_paths = [
        unit_creation_dict_path,
        unit_research_abilities_dict_path,
        unit_trained_from_dict_path,
        upgrade_researched_from_dict_path,
        unit_abilities_dict_path,
        unit_unit_alias_dict_path,
        unit_tech_alias_dict_path,
        all_redirect_abilities_path,
    ]
    init_file_path = os.path.join(dicts_path, "__init__.py")
    init_header = f"""# DO NOT EDIT!
# This file was automatically generated by "{file_name}"
    
    """
    generate_init_file(dict_file_paths=dict_file_paths, file_path=init_file_path, file_header=init_header)

    dump_dict_to_file(
        unit_train_abilities,
        unit_creation_dict_path,
        dict_name="TRAIN_INFO",
        file_header=file_header,
        dict_type_annotation=": Dict[UnitTypeId, Dict[UnitTypeId, Dict[str, Union[AbilityId, bool, UnitTypeId]]]]",
    )
    dump_dict_to_file(
        unit_research_abilities,
        unit_research_abilities_dict_path,
        dict_name="RESEARCH_INFO",
        file_header=file_header,
        dict_type_annotation=": Dict[UnitTypeId, Dict[UpgradeId, Dict[str, Union[AbilityId, bool, UnitTypeId]]]]",
    )
    dump_dict_to_file(
        unit_trained_from,
        unit_trained_from_dict_path,
        dict_name="UNIT_TRAINED_FROM",
        file_header=file_header,
        dict_type_annotation=": Dict[UnitTypeId, Set[UnitTypeId]]",
    )
    dump_dict_to_file(
        upgrade_researched_from,
        upgrade_researched_from_dict_path,
        dict_name="UPGRADE_RESEARCHED_FROM",
        file_header=file_header,
        dict_type_annotation=": Dict[UpgradeId, UnitTypeId]",
    )
    dump_dict_to_file(
        unit_abilities,
        unit_abilities_dict_path,
        dict_name="UNIT_ABILITIES",
        file_header=file_header,
        dict_type_annotation=": Dict[UnitTypeId, Set[AbilityId]]",
    )
    dump_dict_to_file(
        unit_unit_alias,
        unit_unit_alias_dict_path,
        dict_name="UNIT_UNIT_ALIAS",
        file_header=file_header,
        dict_type_annotation=": Dict[UnitTypeId, UnitTypeId]",
    )
    dump_dict_to_file(
        unit_tech_alias,
        unit_tech_alias_dict_path,
        dict_name="UNIT_TECH_ALIAS",
        file_header=file_header,
        dict_type_annotation=": Dict[UnitTypeId, Set[UnitTypeId]]",
    )
    dump_dict_to_file(
        all_redirect_abilities,
        all_redirect_abilities_path,
        dict_name="GENERIC_REDIRECT_ABILITIES",
        file_header=file_header,
        dict_type_annotation=": Dict[AbilityId, AbilityId]",
    )

    # print(unit_train_abilities)


if __name__ == "__main__":
    main()
