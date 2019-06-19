import json, os, subprocess
from typing import Dict, Set, List, Union, Optional

from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.effect_id import EffectId

"""
This script does the following:
- Loop over all abilities, checking what unit they create and if it requires a placement position
- Loop over all units, checking what abilities they have and which of those create units, and what tech requirements they have
- Loop over all all upgrades and get their creation ability, which unit can research it and what building requirements there are
"""


def dump_dict_to_file(
    my_dict: dict, file_path: str, dict_name: str, file_header: str = "", dict_type_annotation: str = ""
):
    # print(str(my_dict))
    # print(repr(my_dict))
    tab = 4 * " "
    with open(file_path, "w") as f:
        f.write(file_header)
        f.write("\n")
        f.write(f"{dict_name}{dict_type_annotation} = ")
        # f.write(f"{dict_name}{dict_type_annotation} = " + "{\n")
        f.write(str(my_dict))
        # f.write("}")

    # Apply formatting if file is too long
    subprocess.run(["black", file_path])


def get_unit_train_build_abilities(data):
    ability_data = data["Ability"]
    unit_data = data["Unit"]
    upgrade_data = data["Upgrade"]

    # From which abilities can a unit be trained
    train_abilities: Dict[UnitTypeId, Set[AbilityId]] = {}
    # If the ability requires a placement position
    ability_requires_placement: Set[AbilityId] = set()
    # Map ability to unittypeid
    ability_to_unittypeid_dict: Dict[AbilityId, UnitTypeId] = {}

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
            }
        ):
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
                "requires_tech_building": UnitTypeId.CYBERNETICSCORE, # Or None
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
    unit_train_abilities: Dict[UnitTypeId, Dict[str, Union[AbilityId, bool, UnitTypeId]]] = {}
    for entry in unit_data:
        unit_abilities = entry.get("abilities", [])
        unit_type = UnitTypeId(entry["id"])
        current_unit_train_abilities = {}
        for ability_info in unit_abilities:
            ability_id_value: int = ability_info.get("ability", 0)
            if ability_id_value:
                ability_id: AbilityId = AbilityId(ability_id_value)
                # Ability is not a train ability
                if ability_id not in ability_to_unittypeid_dict:
                    continue

                requires_techlab: bool = False
                requires_tech_building: Optional[UnitTypeId] = None
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
                        requires_tech_building = UnitTypeId(requires_tech_builing_id_value)

                if ability_id in ability_requires_placement:
                    requires_placement_position = True

                requires_power = entry.get("needs_power", False)

                # Debugging output:

                # if ability_id in {AbilityId.BARRACKSTRAIN_GHOST}:
                #     print(json.dumps(entry, indent=4))

                # TODO: Hotfix for ghost
                if ability_id == AbilityId.BARRACKSTRAIN_GHOST:
                    requires_techlab = True

                resulting_unit = ability_to_unittypeid_dict[ability_id]

                ability_dict = {"ability": ability_id}
                # Only add boolean values and tech requirement if they actually exist, to make the resulting dict file smaller
                if requires_techlab:
                    ability_dict["requires_techlab"] = requires_techlab
                if requires_tech_building:
                    ability_dict["requires_tech_building"] = requires_tech_building
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

    ability_to_upgrade_dict: Dict[AbilityId, UpgradeId] = {}

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
                "requires_tech_building": None,
                "requires_power": False, # If a pylon nearby is required
            },
            UpgradeId.TERRANINFANTRYWEAPONSLEVEL2: {
                "ability": AbilityId.ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL2,
                "requires_tech_building": UnitTypeId.ARMORY,
                "requires_power": False, # If a pylon nearby is required
            },
        }
    }
    """
    unit_research_abilities = {}
    for entry in unit_data:
        unit_abilities = entry.get("abilities", [])
        unit_type = UnitTypeId(entry["id"])

        if unit_type == UnitTypeId.TECHLAB:
            continue

        current_unit_research_abilities = {}
        for ability_info in unit_abilities:
            ability_id_value: int = ability_info.get("ability", 0)
            if ability_id_value:
                ability_id: AbilityId = AbilityId(ability_id_value)
                # Upgrade is not a known upgrade ability
                if ability_id not in ability_to_upgrade_dict:
                    continue

                greater_spire_as_requirement: Set[AbilityId] = {
                    AbilityId.RESEARCH_ZERGFLYERATTACKLEVEL2,
                    AbilityId.RESEARCH_ZERGFLYERATTACKLEVEL3,
                    AbilityId.RESEARCH_ZERGFLYERARMORLEVEL2,
                    AbilityId.RESEARCH_ZERGFLYERARMORLEVEL3,
                }

                required_building = None
                requirements = ability_info.get("requirements", [])
                # TODO: fix for greater spire, wrong in dentosals tech tree (lair and hive instead of greater spire)
                if ability_id in greater_spire_as_requirement:
                    required_building = UnitTypeId.GREATERSPIRE
                elif requirements:
                    req_building_id_value = next(
                        (req["building"] for req in requirements if req.get("building", 0)), None
                    )
                    if req_building_id_value:
                        req_building_id = UnitTypeId(req_building_id_value)
                        required_building = req_building_id

                requires_power = entry.get("needs_power", False)

                resulting_upgrade = ability_to_upgrade_dict[ability_id]

                research_info = {
                    "ability": ability_id,
                }
                if required_building:
                    research_info["required_building"] = required_building
                if requires_power:
                    research_info["requires_power"] = requires_power
                current_unit_research_abilities[resulting_upgrade] = research_info

        # TODO: Fix liberator range upgrade, missing in dentosals techtree
        if unit_type == UnitTypeId.STARPORTTECHLAB:
            current_unit_research_abilities[UpgradeId.LIBERATORMORPH] = {
                "upgrade": UpgradeId.LIBERATORMORPH,
                "ability": AbilityId.STARPORTTECHLABRESEARCH_RESEARCHLIBERATORAGMODE,
                "requires_tech_building": UnitTypeId.FUSIONCORE,
            }

        # TODO: Fix lurker den adaptive talons, missing in dentosals techtree
        if unit_type == UnitTypeId.LURKERDENMP:
            current_unit_research_abilities[UpgradeId.DIGGINGCLAWS] = {
                "upgrade": UpgradeId.DIGGINGCLAWS,
                "ability": AbilityId.RESEARCH_ADAPTIVETALONS,
                "requires_tech_building": UnitTypeId.HIVE,
            }

        if current_unit_research_abilities:
            unit_research_abilities[unit_type] = current_unit_research_abilities

    # TODO: Hotfix for greater spire - currently only level 1 research abilities are listed in greater spire (dentosals tech tree), but 1 to 3 are listed in spire
    unit_research_abilities[UnitTypeId.GREATERSPIRE] = unit_research_abilities[UnitTypeId.SPIRE]

    return unit_research_abilities

def get_unit_created_from(unit_train_abilities: dict):
    unit_created_from = {}

    for creator_unit, create_abilities in unit_train_abilities.items():
        for created_unit, create_info in create_abilities.items():
            if created_unit not in unit_created_from:
                unit_created_from[created_unit] = set()
            unit_created_from[created_unit].add(creator_unit)

    return unit_created_from


def get_upgrade_researched_from(unit_research_abilities: dict):
    upgrade_researched_from = {}

    for researcher_unit, research_abilities in unit_research_abilities.items():
        for upgrade, research_info in research_abilities.items():
            upgrade_researched_from[upgrade] = researcher_unit

    return upgrade_researched_from


def get_unit_abilities(data: dict):
    ability_data = data["Ability"]
    unit_data = data["Unit"]
    upgrade_data = data["Upgrade"]

    all_unit_abilities: Dict[UnitTypeId, Set[AbilityId]] = {}
    entry: dict
    for entry in unit_data:
        entry_unit_abilities = entry.get("abilities", [])
        unit_type = UnitTypeId(entry["id"])
        current_collected_unit_abilities: Set[AbilityId] = set()
        for ability_info in entry_unit_abilities:
            ability_id_value: int = ability_info.get("ability", 0)
            if ability_id_value:
                ability_id: AbilityId = AbilityId(ability_id_value)
                current_collected_unit_abilities.add(ability_id)

        # print(unit_type, current_unit_abilities)
        if current_collected_unit_abilities:
            all_unit_abilities[unit_type] = current_collected_unit_abilities
    return all_unit_abilities

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

    file_name = os.path.basename(__file__)
    file_header = f"""
# THIS FILE WAS AUTOMATICALLY GENERATED BY "{file_name}" DO NOT CHANGE MANUALLY!
# ANY CHANGE WILL BE OVERWRITTEN

from ..ids.unit_typeid import UnitTypeId
from ..ids.ability_id import AbilityId
from ..ids.upgrade_id import UpgradeId
# from ..ids.buff_id import BuffId
# from ..ids.effect_id import EffectId

from typing import Dict, List, Set, Union
    """

    dump_dict_to_file(
        unit_train_abilities,
        unit_creation_dict_path,
        dict_name="TRAIN_INFO",
        file_header=file_header,
        dict_type_annotation=": Dict[UnitTypeId, Dict[UnitTypeId, Union[AbilityId, bool, UnitTypeId]]]",
    )
    dump_dict_to_file(
        unit_research_abilities,
        unit_research_abilities_dict_path,
        dict_name="RESEARCH_INFO",
        file_header=file_header,
        dict_type_annotation=": Dict[UnitTypeId, Dict[UpgradeId, Union[AbilityId, bool, UnitTypeId]]]",
    )
    dump_dict_to_file(
        unit_trained_from,
        unit_trained_from_dict_path,
        dict_name="UNIT_TRAINED_FROM",
        file_header=file_header,
        dict_type_annotation=": Dict[UnitTypeId, UnitTypeId]",
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

    # print(unit_train_abilities)


if __name__ == "__main__":
    main()
