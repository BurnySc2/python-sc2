from __future__ import annotations
from typing import Any, Dict, List, Optional, Set, Tuple, Union, TYPE_CHECKING

from . import unit as unit_module
from .ids.ability_id import AbilityId
from .position import Point2
from .constants import COMBINEABLE_ABILITIES

from typing import Union

if TYPE_CHECKING:
    from .unit import Unit

class UnitCommand:
    def __init__(self, ability: AbilityId, unit: Unit, target: Union[Unit, Point2] = None, queue: bool = False):
        """
        :param ability:
        :param unit:
        :param target:
        :param queue:
        """
        assert ability in AbilityId, f"ability {ability} is not in AbilityId"
        assert isinstance(unit, unit_module.Unit), f"unit {unit} is of type {type(unit)}"
        assert target is None or isinstance(
            target, (Point2, unit_module.Unit)
        ), f"target {target} is of type {type(target)}"
        assert isinstance(queue, bool), f"queue flag {queue} is of type {type(queue)}"
        self.ability = ability
        self.unit = unit
        self.target = target
        self.queue = queue

    @property
    def combining_tuple(self):
        return (self.ability, self.target, self.queue, self.ability in COMBINEABLE_ABILITIES)

    def __repr__(self):
        return f"UnitCommand({self.ability}, {self.unit}, {self.target}, {self.queue})"
