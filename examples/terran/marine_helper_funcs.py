import asyncio
import os
import sys
import json
from collections import OrderedDict

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.main import run_game

from baselines.common.atari_wrappers import make_atari, wrap_deepmind
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.utils import plot_model

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import numpy as np

from sc2.data import Difficulty, Race, Result
from sc2.player import Bot, Computer
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.units import Units

import time
import pandas as pd
import aiofiles
from aiocsv import AsyncReader, AsyncDictReader, AsyncWriter, AsyncDictWriter
import csv

from tensorflow import keras
import tensorflow as tf

# https://www.youtube.com/watch?v=1-QtVxce44k&ab_channel=Altercate


def calc_value_func(marine_health_list):
    """
    my sum of marine health minus the sum of enemy marine's health
    """
    return np.sum(
        marine_health_list[0: int(len(marine_health_list)/2)]
    ) - np.sum(
        marine_health_list[int(len(marine_health_list)/2):]
    )


def attack_nearest(bot, marine_health_dict):
    for marine in bot.units(UnitTypeId.MARINE):
        marine.attack(
            bot.enemy_units.closest_n_units(bot.start_location, n=1)[0]
        )
        marine_health_dict[marine.tag] = marine.health
        bot.marine_tags_list.append(marine.tag)
    return marine_health_dict

def attack_nearest_max_allocation(bot, max_allocation=3):
    friendly_marines_list = list(bot.units(UnitTypeId.MARINE))
    friendly_marines_num = len(friendly_marines_list)

    # at each step, attack enough enemies that we have at most max_allocation per enemy
    #print(f'attacking {int(np.ceil(friendly_marines_num / max_allocation))} enemies with {friendly_marines_num} marines')
    enemy_marines_to_attack = bot.enemy_units.closest_n_units(
        bot.start_location,
        n=int(np.ceil(friendly_marines_num / max_allocation))
    )

    # split friendly marines for each enemy
    if len(friendly_marines_list) == 0 or len(enemy_marines_to_attack) == 0:
        return
    else:
        friendly_marine_groups = np.array_split(friendly_marines_list, len(enemy_marines_to_attack))

    for group_num, friendly_marine_group in enumerate(friendly_marine_groups):
        for marine in friendly_marine_group:
            marine.attack(
                enemy_marines_to_attack[group_num]
            )
            #marine_health_dict[marine.tag] = marine.health
            #bot.marine_tags_list.append(marine.tag)
    return
    #return marine_health_dict


def attack_nearest_max_allocation_tf(bot, max_allocation=3, marine_tag_list=None):
    if marine_tag_list is None:
        raise ValueError("marien tag list should not be None")

    # create the action dict according to the marine tag list with the tag order
    # (so that actions will be attached to the right marine)
    actions_dict = OrderedDict({tag: None for tag in marine_tag_list })

    friendly_marines_list = list(bot.units(UnitTypeId.MARINE))
    friendly_marines_num = len(friendly_marines_list)

    # at each step, attack enough enemies that we have at most max_allocation per enemy
    #print(f'attacking {int(np.ceil(friendly_marines_num / max_allocation))} enemies with {friendly_marines_num} marines')
    enemy_marines_to_attack = bot.enemy_units.closest_n_units(
        bot.start_location,
        n=int(np.ceil(friendly_marines_num / max_allocation))
    )

    # split friendly marines for each enemy
    if len(friendly_marines_list) == 0 or len(enemy_marines_to_attack) == 0:
        return np.array([None]*8)
    else:
        friendly_marine_groups = np.array_split(friendly_marines_list, len(enemy_marines_to_attack))

    for group_num, friendly_marine_group in enumerate(friendly_marine_groups):
        for marine in friendly_marine_group:
            marine.attack(
                enemy_marines_to_attack[group_num]
            )
            actions_dict[marine.tag] = enemy_marines_to_attack[group_num].tag

    return actions_dict


def build_ordered_marine_tag_list(bot : BotAI):
    marine_tag_list = []
    marine_friendly_tag_list = []
    marine_enemy_tag_list = []

    for unit in bot.units.closest_n_units(bot.start_location, n=40):
        if unit.type_id == UnitTypeId.MARINE:
            marine_tag_list.append(unit.tag)
            marine_friendly_tag_list.append(unit.tag)

    for unit in bot.enemy_units.closest_n_units(bot.start_location, n=40):
        if unit.type_id == UnitTypeId.MARINE:
            marine_tag_list.append(unit.tag)
            marine_enemy_tag_list.append(unit.tag)

    return marine_tag_list, marine_friendly_tag_list, marine_enemy_tag_list


def observe_health(bot, marine_tag_list):
    marine_health_dict = OrderedDict()

    for tag in marine_tag_list:
        marine_health_dict[tag] = 0.0

    are_there_friendly_marines = False
    are_there_enemy_marines = False

    for marine in bot.units(UnitTypeId.MARINE):
        marine_health_dict[marine.tag] = marine.health
        are_there_friendly_marines = True

    #enemy_marine_health_dict = {}
    for enemy_marine in bot.enemy_units(UnitTypeId.MARINE):
        marine_health_dict[enemy_marine.tag] = enemy_marine.health
        are_there_enemy_marines = True

    #marine_health_dict.update(enemy_marine_health_dict)

    return marine_health_dict, are_there_friendly_marines, are_there_enemy_marines


def observe_health_ordered(bot, state_map_list):
    marine_health_dict = OrderedDict()

    are_there_friendly_marines = False
    are_there_enemy_marines = False

    for marine in bot.units(UnitTypeId.MARINE):
        marine_health_dict[marine.tag] = marine.health
        are_there_friendly_marines = True

    #enemy_marine_health_dict = {}
    for enemy_marine in bot.enemy_units(UnitTypeId.MARINE):
        marine_health_dict[enemy_marine.tag] = enemy_marine.health
        are_there_enemy_marines = True

    #marine_health_dict.update(enemy_marine_health_dict)

    return marine_health_dict, are_there_friendly_marines, are_there_enemy_marines


def translate_actions_dict_to_array(marine_friendly_tag_list: list, marine_enemy_tag_list: list, action_dict: OrderedDict):
    """
    marine_tag_list has a list of marines tag, such that the first half is friendly marines
        ordered by closeness to starting position. The second half is enemy marines ordered
        by the same way
    action_dict is simply a map between friendly marine tags to enemy marines tag that they are ordered to attack.

    This function we return a 2D numpy array such that the i-th marine attacked the j-th enemy marine will have a
        1 value, otherwise it's all 0s.
    """
    action_array = np.ones(
        (len(marine_friendly_tag_list), len(marine_enemy_tag_list))
    )*np.nan

    for friendly_tag, enemy_tag in action_dict.items():
        action_array[marine_friendly_tag_list.index(friendly_tag), :] = 0
        action_array[marine_friendly_tag_list.index(friendly_tag), marine_enemy_tag_list.index(enemy_tag)] = 0

    return action_array


def create_q_model():
    # Network defined by the Deepmind paper
    inputs = layers.Input(shape=(16, 1, 1,))
    num_friendly_marines = 8
    num_eneymy_marines = 8
    num_actions = num_friendly_marines * num_eneymy_marines

    # Convolutions on the frames on the screen
    layer1 = layers.Flatten()(inputs)
    layer2 = layers.Dense(64, activation="relu")(layer1)
    layer3 = layers.Dense(num_actions, activation="relu")(layer2)
    layer4 = layers.Reshape((num_friendly_marines, num_eneymy_marines, 1))(layer3)
    action = layers.Softmax(axis=1)(layer4)

    return keras.Model(inputs=inputs, outputs=action)


