from itertools import groupby

from s2clientprotocol import common_pb2 as common_pb
from s2clientprotocol import raw_pb2 as raw_pb

from .position import Point2
from .unit import Unit


def combine_actions(action_iter):
    """
    Example input:
    [
        # Each entry in the list is a unit command, with an ability, unit, target, and queue=boolean
        UnitCommand(AbilityId.TRAINQUEEN_QUEEN, Unit(name='Hive', tag=4353687554), None, False),
        UnitCommand(AbilityId.TRAINQUEEN_QUEEN, Unit(name='Lair', tag=4359979012), None, False),
        UnitCommand(AbilityId.TRAINQUEEN_QUEEN, Unit(name='Hatchery', tag=4359454723), None, False),
    ]
    """
    for key, items in groupby(action_iter, key=lambda a: a.combining_tuple):
        ability, target, queue = key

        if target is None:
            cmd = raw_pb.ActionRawUnitCommand(
                ability_id=ability.value, unit_tags={u.unit.tag for u in items}, queue_command=queue
            )
        elif isinstance(target, Point2):
            cmd = raw_pb.ActionRawUnitCommand(
                ability_id=ability.value,
                unit_tags={u.unit.tag for u in items},
                queue_command=queue,
                target_world_space_pos=common_pb.Point2D(x=target.x, y=target.y),
            )
        elif isinstance(target, Unit):
            cmd = raw_pb.ActionRawUnitCommand(
                ability_id=ability.value,
                unit_tags={u.unit.tag for u in items},
                queue_command=queue,
                target_unit_tag=target.tag,
            )
        else:
            raise RuntimeError(f"Must target a unit, point or None, found '{target !r}'")

        yield raw_pb.ActionRaw(unit_command=cmd)
