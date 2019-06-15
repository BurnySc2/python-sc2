from __future__ import annotations
import logging
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union, TYPE_CHECKING

from s2clientprotocol import common_pb2 as common_pb
from s2clientprotocol import debug_pb2 as debug_pb
from s2clientprotocol import query_pb2 as query_pb
from s2clientprotocol import raw_pb2 as raw_pb
from s2clientprotocol import sc2api_pb2 as sc_pb

from .action import combine_actions
from .data import ActionResult, ChatChannel, Race, Result, Status
from .game_data import AbilityData, GameData
from .game_info import GameInfo
from .ids.ability_id import AbilityId
from .ids.unit_typeid import UnitTypeId
from .position import Point2, Point3
from .protocol import Protocol, ProtocolError
from .renderer import Renderer
from .unit import Unit
from .units import Units

logger = logging.getLogger(__name__)


class Client(Protocol):
    def __init__(self, ws):
        """
        :param ws:
        """
        super().__init__(ws)
        self.game_step = 8
        self._player_id = None
        self._game_result = None
        self._debug_texts = []
        self._debug_lines = []
        self._debug_boxes = []
        self._debug_spheres = []
        self._debug_draw_last_frame = False

        self._renderer = None

    @property
    def in_game(self):
        return self._status == Status.in_game

    async def join_game(self, name=None, race=None, observed_player_id=None, portconfig=None, rgb_render_config=None):
        ifopts = sc_pb.InterfaceOptions(
            raw=True, score=True, show_cloaked=True, raw_affects_selection=False, raw_crop_to_playable_area=False
        )

        if rgb_render_config:
            assert isinstance(rgb_render_config, dict)
            assert "window_size" in rgb_render_config and "minimap_size" in rgb_render_config
            window_size = rgb_render_config["window_size"]
            minimap_size = rgb_render_config["minimap_size"]
            self._renderer = Renderer(self, window_size, minimap_size)
            map_width, map_height = window_size
            minimap_width, minimap_height = minimap_size

            ifopts.render.resolution.x = map_width
            ifopts.render.resolution.y = map_height
            ifopts.render.minimap_resolution.x = minimap_width
            ifopts.render.minimap_resolution.y = minimap_height

        if race is None:
            assert isinstance(observed_player_id, int), f"observed_player_id is of type {type(observed_player_id)}"
            # join as observer
            req = sc_pb.RequestJoinGame(observed_player_id=observed_player_id, options=ifopts)
        else:
            assert isinstance(race, Race)
            req = sc_pb.RequestJoinGame(race=race.value, options=ifopts)

        if portconfig:
            req.shared_port = portconfig.shared
            req.server_ports.game_port = portconfig.server[0]
            req.server_ports.base_port = portconfig.server[1]

            for ppc in portconfig.players:
                p = req.client_ports.add()
                p.game_port = ppc[0]
                p.base_port = ppc[1]

        if name is not None:
            assert isinstance(name, str), f"name is of type {type(name)}"
            req.player_name = name

        result = await self._execute(join_game=req)
        self._game_result = None
        self._player_id = result.join_game.player_id
        return result.join_game.player_id

    async def leave(self):
        """ You can use 'await self._client.leave()' to surrender midst game. """
        is_resign = self._game_result is None

        if is_resign:
            # For all clients that can leave, result of leaving the game either
            # loss, or the client will ignore the result
            self._game_result = {self._player_id: Result.Defeat}

        try:
            await self._execute(leave_game=sc_pb.RequestLeaveGame())
        except ProtocolError:
            if is_resign:
                raise

    async def save_replay(self, path):
        logger.debug(f"Requesting replay from server")
        result = await self._execute(save_replay=sc_pb.RequestSaveReplay())
        with open(path, "wb") as f:
            f.write(result.save_replay.data)
        logger.info(f"Saved replay to {path}")

    async def observation(self):
        result = await self._execute(observation=sc_pb.RequestObservation())
        assert result.HasField("observation")

        if not self.in_game or result.observation.player_result:
            # Sometimes game ends one step before results are available
            if not result.observation.player_result:
                result = await self._execute(observation=sc_pb.RequestObservation())
                assert result.observation.player_result

            player_id_to_result = {}
            for pr in result.observation.player_result:
                player_id_to_result[pr.player_id] = Result(pr.result)
            self._game_result = player_id_to_result

        # if render_data is available, then RGB rendering was requested
        if self._renderer and result.observation.observation.HasField("render_data"):
            await self._renderer.render(result.observation)

        return result

    async def step(self):
        """ EXPERIMENTAL: Change self._client.game_step during the step function to increase or decrease steps per second """
        return await self._execute(step=sc_pb.RequestStep(count=self.game_step))

    async def get_game_data(self) -> GameData:
        result = await self._execute(
            data=sc_pb.RequestData(ability_id=True, unit_type_id=True, upgrade_id=True, buff_id=True, effect_id=True)
        )
        return GameData(result.data)

    async def dump_data(self, ability_id=True, unit_type_id=True, upgrade_id=True, buff_id=True, effect_id=True):
        """
        Dump the game data files
        choose what data to dump in the keywords
        this function writes to a text file
        call it one time in on_step with:
        await self._client.dump_data()
        """
        result = await self._execute(
            data=sc_pb.RequestData(
                ability_id=ability_id,
                unit_type_id=unit_type_id,
                upgrade_id=upgrade_id,
                buff_id=buff_id,
                effect_id=effect_id,
            )
        )
        with open("data_dump.txt", "a") as file:
            file.write(str(result.data))

    async def get_game_info(self) -> GameInfo:
        result = await self._execute(game_info=sc_pb.RequestGameInfo())
        return GameInfo(result.game_info)

    async def actions(self, actions, return_successes=False):
        if not actions:
            return None
        elif not isinstance(actions, list):
            actions = [actions]
        res = await self._execute(
            action=sc_pb.RequestAction(actions=(sc_pb.Action(action_raw=a) for a in combine_actions(actions)))
        )
        if return_successes:
            return [ActionResult(r) for r in res.action.result]
        else:
            return [ActionResult(r) for r in res.action.result if ActionResult(r) != ActionResult.Success]

    async def query_pathing(
        self, start: Union[Unit, Point2, Point3], end: Union[Point2, Point3]
    ) -> Optional[Union[int, float]]:
        """ Caution: returns "None" when path not found
        Try to combine queries with the function below because the pathing query is generally slow.

        :param start:
        :param end: """
        assert isinstance(start, (Point2, Unit))
        assert isinstance(end, Point2)
        if isinstance(start, Point2):
            result = await self._execute(
                query=query_pb.RequestQuery(
                    pathing=[
                        query_pb.RequestQueryPathing(
                            start_pos=common_pb.Point2D(x=start.x, y=start.y),
                            end_pos=common_pb.Point2D(x=end.x, y=end.y),
                        )
                    ]
                )
            )
        else:
            result = await self._execute(
                query=query_pb.RequestQuery(
                    pathing=[
                        query_pb.RequestQueryPathing(unit_tag=start.tag, end_pos=common_pb.Point2D(x=end.x, y=end.y))
                    ]
                )
            )
        distance = float(result.query.pathing[0].distance)
        if distance <= 0.0:
            return None
        return distance

    async def query_pathings(self, zipped_list: List[List[Union[Unit, Point2, Point3]]]) -> List[Union[float, int]]:
        """ Usage: await self.query_pathings([[unit1, target2], [unit2, target2]])
        -> returns [distance1, distance2]
        Caution: returns 0 when path not found

        :param zipped_list:
        """
        assert zipped_list, "No zipped_list"
        assert isinstance(zipped_list, list), f"{type(zipped_list)}"
        assert isinstance(zipped_list[0], list), f"{type(zipped_list[0])}"
        assert len(zipped_list[0]) == 2, f"{len(zipped_list[0])}"
        assert isinstance(zipped_list[0][0], (Point2, Unit)), f"{type(zipped_list[0][0])}"
        assert isinstance(zipped_list[0][1], Point2), f"{type(zipped_list[0][1])}"
        if isinstance(zipped_list[0][0], Point2):
            results = await self._execute(
                query=query_pb.RequestQuery(
                    pathing=(
                        query_pb.RequestQueryPathing(
                            start_pos=common_pb.Point2D(x=p1.x, y=p1.y), end_pos=common_pb.Point2D(x=p2.x, y=p2.y)
                        )
                        for p1, p2 in zipped_list
                    )
                )
            )
        else:
            results = await self._execute(
                query=query_pb.RequestQuery(
                    pathing=(
                        query_pb.RequestQueryPathing(unit_tag=p1.tag, end_pos=common_pb.Point2D(x=p2.x, y=p2.y))
                        for p1, p2 in zipped_list
                    )
                )
            )
        return [float(d.distance) for d in results.query.pathing]

    async def query_building_placement(
        self, ability: AbilityData, positions: List[Union[Point2, Point3]], ignore_resources: bool = True
    ) -> List[ActionResult]:
        assert isinstance(ability, AbilityData)
        result = await self._execute(
            query=query_pb.RequestQuery(
                placements=(
                    query_pb.RequestQueryBuildingPlacement(
                        ability_id=ability.id.value, target_pos=common_pb.Point2D(x=position.x, y=position.y)
                    )
                    for position in positions
                ),
                ignore_resource_requirements=ignore_resources,
            )
        )
        return [ActionResult(p.result) for p in result.query.placements]

    async def query_available_abilities(
        self, units: Union[List[Unit], Units], ignore_resource_requirements: bool = False
    ) -> List[List[AbilityId]]:
        """ Query abilities of multiple units """
        input_was_a_list = True
        if not isinstance(units, list):
            """ Deprecated, accepting a single unit may be removed in the future, query a list of units instead """
            assert isinstance(units, Unit)
            units = [units]
            input_was_a_list = False
        assert units
        result = await self._execute(
            query=query_pb.RequestQuery(
                abilities=(query_pb.RequestQueryAvailableAbilities(unit_tag=unit.tag) for unit in units),
                ignore_resource_requirements=ignore_resource_requirements,
            )
        )
        """ Fix for bots that only query a single unit, may be removed soon """
        if not input_was_a_list:
            return [[AbilityId(a.ability_id) for a in b.abilities] for b in result.query.abilities][0]
        return [[AbilityId(a.ability_id) for a in b.abilities] for b in result.query.abilities]

    async def chat_send(self, message: str, team_only: bool):
        """ Writes a message to the chat """
        ch = ChatChannel.Team if team_only else ChatChannel.Broadcast
        await self._execute(
            action=sc_pb.RequestAction(
                actions=[sc_pb.Action(action_chat=sc_pb.ActionChat(channel=ch.value, message=message))]
            )
        )

    async def toggle_autocast(self, units: Union[List[Unit], Units], ability: AbilityId):
        """ Toggle autocast of all specified units

        :param units:
        :param ability: """
        assert units
        assert isinstance(units, list)
        assert all(isinstance(u, Unit) for u in units)
        assert isinstance(ability, AbilityId)

        await self._execute(
            action=sc_pb.RequestAction(
                actions=[
                    sc_pb.Action(
                        action_raw=raw_pb.ActionRaw(
                            toggle_autocast=raw_pb.ActionRawToggleAutocast(
                                ability_id=ability.value, unit_tags=(u.tag for u in units)
                            )
                        )
                    )
                ]
            )
        )

    async def debug_create_unit(self, unit_spawn_commands: List[List[Union[UnitTypeId, int, Point2, Point3]]]):
        """ Usage example (will spawn 5 marines in the center of the map for player ID 1):
        await self._client.debug_create_unit([[UnitTypeId.MARINE, 5, self._game_info.map_center, 1]])

        :param unit_spawn_commands: """
        assert isinstance(unit_spawn_commands, list)
        assert unit_spawn_commands
        assert isinstance(unit_spawn_commands[0], list)
        assert len(unit_spawn_commands[0]) == 4
        assert isinstance(unit_spawn_commands[0][0], UnitTypeId)
        assert unit_spawn_commands[0][1] > 0  # careful, in realtime=True this function may create more units
        assert isinstance(unit_spawn_commands[0][2], (Point2, Point3))
        assert 1 <= unit_spawn_commands[0][3] <= 2

        await self._execute(
            debug=sc_pb.RequestDebug(
                debug=(
                    debug_pb.DebugCommand(
                        create_unit=debug_pb.DebugCreateUnit(
                            unit_type=unit_type.value,
                            owner=owner_id,
                            pos=common_pb.Point2D(x=position.x, y=position.y),
                            quantity=amount_of_units,
                        )
                    )
                    for unit_type, amount_of_units, position, owner_id in unit_spawn_commands
                )
            )
        )

    async def debug_kill_unit(self, unit_tags: Union[Unit, Units, List[int], Set[int]]):
        """
        :param unit_tags:
        """
        if isinstance(unit_tags, Units):
            unit_tags = unit_tags.tags
        if isinstance(unit_tags, Unit):
            unit_tags = [unit_tags.tag]
        assert unit_tags

        await self._execute(
            debug=sc_pb.RequestDebug(debug=[debug_pb.DebugCommand(kill_unit=debug_pb.DebugKillUnit(tag=unit_tags))])
        )

    async def move_camera(self, position: Union[Unit, Units, Point2, Point3]):
        """ Moves camera to the target position """
        assert isinstance(position, (Unit, Units, Point2, Point3))
        if isinstance(position, Units):
            position = position.center
        if isinstance(position, Unit):
            position = position.position
        await self._execute(
            action=sc_pb.RequestAction(
                actions=[
                    sc_pb.Action(
                        action_raw=raw_pb.ActionRaw(
                            camera_move=raw_pb.ActionRawCameraMove(
                                center_world_space=common_pb.Point(x=position.x, y=position.y)
                            )
                        )
                    )
                ]
            )
        )

    async def move_camera_spatial(self, position: Union[Point2, Point3]):
        """ Moves camera to the target position using the spatial aciton interface

        :param position: """
        from s2clientprotocol import spatial_pb2 as spatial_pb

        assert isinstance(position, (Point2, Point3))
        action = sc_pb.Action(
            action_render=spatial_pb.ActionSpatial(
                camera_move=spatial_pb.ActionSpatialCameraMove(
                    center_minimap=common_pb.PointI(x=position.x, y=position.y)
                )
            )
        )
        await self._execute(action=sc_pb.RequestAction(actions=[action]))

    def debug_text_simple(self, text: str):
        """ Draws a text in the top left corner of the screen (up to a max of 6 messages it seems). """
        self._debug_texts.append(self.to_debug_message(text))

    def debug_text_screen(self, text: str, pos: Union[Point2, Point3, tuple, list], color=None, size: int = 8):
        """ Draws a text on the screen with coordinates 0 <= x, y <= 1. """
        assert len(pos) >= 2
        assert 0 <= pos[0] <= 1
        assert 0 <= pos[1] <= 1
        pos = Point2((pos[0], pos[1]))
        self._debug_texts.append(self.to_debug_message(text, color, pos, size))

    def debug_text_2d(self, text: str, pos: Union[Point2, Point3, tuple, list], color=None, size: int = 8):
        return self.debug_text_screen(text, pos, color, size)

    def debug_text_world(self, text: str, pos: Union[Unit, Point2, Point3], color=None, size: int = 8):
        """ Draws a text at Point3 position. Don't forget to add 'await self._client.send_debug'.
        To grab a unit's 3d position, use unit.position3d
        Usually the Z value of a Point3 is between 8 and 14 (except for flying units)
        """
        if isinstance(pos, Point2) and not isinstance(pos, Point3):  # a Point3 is also a Point2
            pos = Point3((pos.x, pos.y, 0))
        self._debug_texts.append(self.to_debug_message(text, color, pos, size))

    def debug_text_3d(self, text: str, pos: Union[Unit, Point2, Point3], color=None, size: int = 8):
        return self.debug_text_world(text, pos, color, size)

    def debug_line_out(self, p0: Union[Unit, Point2, Point3], p1: Union[Unit, Point2, Point3], color=None):
        """ Draws a line from p0 to p1. """
        self._debug_lines.append(
            debug_pb.DebugLine(
                line=debug_pb.Line(p0=self.to_debug_point(p0), p1=self.to_debug_point(p1)),
                color=self.to_debug_color(color),
            )
        )

    def debug_box_out(self, p_min: Union[Unit, Point2, Point3], p_max: Union[Unit, Point2, Point3], color=None):
        """ Draws a box with p_min and p_max as corners. """
        self._debug_boxes.append(
            debug_pb.DebugBox(
                min=self.to_debug_point(p_min), max=self.to_debug_point(p_max), color=self.to_debug_color(color)
            )
        )

    def debug_sphere_out(self, p: Union[Unit, Point2, Point3], r: Union[int, float], color=None):
        """ Draws a sphere at point p with radius r. """
        self._debug_spheres.append(
            debug_pb.DebugSphere(p=self.to_debug_point(p), r=r, color=self.to_debug_color(color))
        )

    async def _send_debug(self):
        """ Sends the debug draw execution. This is run by main.py now automatically, if there is any items in the list. You do not need to run this manually any longer. """
        if self._debug_texts or self._debug_lines or self._debug_boxes or self._debug_spheres:
            await self._execute(
                debug=sc_pb.RequestDebug(
                    debug=[
                        debug_pb.DebugCommand(
                            draw=debug_pb.DebugDraw(
                                text=self._debug_texts if self._debug_texts else None,
                                lines=self._debug_lines if self._debug_lines else None,
                                boxes=self._debug_boxes if self._debug_boxes else None,
                                spheres=self._debug_spheres if self._debug_spheres else None,
                            )
                        )
                    ]
                )
            )
            self._debug_draw_last_frame = True
            self._debug_texts.clear()
            self._debug_lines.clear()
            self._debug_boxes.clear()
            self._debug_spheres.clear()
        elif self._debug_draw_last_frame:
            # Clear drawing if we drew last frame but nothing to draw this frame
            await self._execute(
                debug=sc_pb.RequestDebug(
                    debug=[
                        debug_pb.DebugCommand(draw=debug_pb.DebugDraw(text=None, lines=None, boxes=None, spheres=None))
                    ]
                )
            )
            self._debug_draw_last_frame = False

    def to_debug_color(self, color):
        """ Helper function for color conversion """
        if color is None:
            return debug_pb.Color(r=255, g=255, b=255)
        # Need to check if not of type Point3 because Point3 inherits from tuple
        elif isinstance(color, (tuple, list)) and not isinstance(color, Point3) and len(color) == 3:
            return debug_pb.Color(r=color[0], g=color[1], b=color[2])
        # In case color is of type Point3
        else:
            r = getattr(color, "r", getattr(color, "x", 255))
            g = getattr(color, "g", getattr(color, "y", 255))
            b = getattr(color, "b", getattr(color, "z", 255))
            if max(r, g, b) <= 1:
                r *= 255
                g *= 255
                b *= 255

            return debug_pb.Color(r=int(r), g=int(g), b=int(b))

    def to_debug_point(self, point: Union[Unit, Point2, Point3]) -> common_pb.Point:
        """ Helper function for point conversion """
        if isinstance(point, Unit):
            point = point.position3d
        return common_pb.Point(x=point.x, y=point.y, z=getattr(point, "z", 0))

    def to_debug_message(
        self, text: str, color=None, pos: Optional[Union[Point2, Point3]] = None, size: int = 8
    ) -> debug_pb.DebugText:
        """ Helper function to create debug texts """
        color = self.to_debug_color(color)
        pt3d = self.to_debug_point(pos) if isinstance(pos, Point3) else None
        virtual_pos = self.to_debug_point(pos) if pos is not None and not isinstance(pos, Point3) else None

        return debug_pb.DebugText(color=color, text=text, virtual_pos=virtual_pos, world_pos=pt3d, size=size)

    async def debug_leave(self):
        await self._execute(debug=sc_pb.RequestDebug(debug=[debug_pb.DebugCommand(end_game=debug_pb.DebugEndGame())]))

    async def debug_set_unit_value(self, unit_tags: Union[Iterable[int], Units, Unit], unit_value: int, value: float):
        """ Sets a "unit value" (Energy, Life or Shields) of the given units to the given value.
        Can't set the life of a unit to 0, use "debug_kill_unit" for that. Also can't set the life above the unit's maximum.
        The following example sets the health of all your workers to 1:
        await self.debug_set_unit_value(self.workers, 2, value=1) """
        if isinstance(unit_tags, Units):
            unit_tags = unit_tags.tags
        if isinstance(unit_tags, Unit):
            unit_tags = [unit_tags.tag]
        assert hasattr(
            unit_tags, "__iter__"
        ), f"unit_tags argument needs to be an iterable (list, dict, set, Units), given argument is {type(unit_tags).__name__}"
        assert (
            1 <= unit_value <= 3
        ), f"unit_value needs to be between 1 and 3 (1 for energy, 2 for life, 3 for shields), given argument is {unit_value}"
        assert all(tag > 0 for tag in unit_tags), f"Unit tags have invalid value: {unit_tags}"
        assert isinstance(value, (int, float)), "Value needs to be of type int or float"
        assert value >= 0, "Value can't be negative"
        await self._execute(
            debug=sc_pb.RequestDebug(
                debug=(
                    debug_pb.DebugCommand(
                        unit_value=debug_pb.DebugSetUnitValue(
                            unit_value=unit_value, value=float(value), unit_tag=unit_tag
                        )
                    )
                    for unit_tag in unit_tags
                )
            )
        )

    async def debug_hang(self, delay_in_seconds: float):
        """ Freezes the SC2 client. Not recommended to be used. """
        delay_in_ms = int(round(delay_in_seconds * 1000))
        await self._execute(
            debug=sc_pb.RequestDebug(
                debug=[debug_pb.DebugCommand(test_process=debug_pb.DebugTestProcess(test=1, delay_ms=delay_in_ms))]
            )
        )

    async def debug_show_map(self):
        """ Reveals the whole map for the bot. Using it a second time disables it again. """
        await self._execute(debug=sc_pb.RequestDebug(debug=[debug_pb.DebugCommand(game_state=1)]))

    async def debug_control_enemy(self):
        """ Allows control over enemy units and structures similar to team games control - does not allow the bot to spend the opponent's ressources. Using it a second time disables it again.  """
        await self._execute(debug=sc_pb.RequestDebug(debug=[debug_pb.DebugCommand(game_state=2)]))

    async def debug_food(self):
        """ Should disable food usage (does not seem to work?). Using it a second time disables it again.  """
        await self._execute(debug=sc_pb.RequestDebug(debug=[debug_pb.DebugCommand(game_state=3)]))

    async def debug_free(self):
        """ Units, structures and upgrades are free of mineral and gas cost. Using it a second time disables it again.  """
        await self._execute(debug=sc_pb.RequestDebug(debug=[debug_pb.DebugCommand(game_state=4)]))

    async def debug_all_resources(self):
        """ Gives 5000 minerals and 5000 vespene to the bot. """
        await self._execute(debug=sc_pb.RequestDebug(debug=[debug_pb.DebugCommand(game_state=5)]))

    async def debug_god(self):
        """ Your units and structures no longer take any damage. Using it a second time disables it again. """
        await self._execute(debug=sc_pb.RequestDebug(debug=[debug_pb.DebugCommand(game_state=6)]))

    async def debug_minerals(self):
        """ Gives 5000 minerals to the bot. """
        await self._execute(debug=sc_pb.RequestDebug(debug=[debug_pb.DebugCommand(game_state=7)]))

    async def debug_gas(self):
        """ Gives 5000 vespene to the bot. """
        await self._execute(debug=sc_pb.RequestDebug(debug=[debug_pb.DebugCommand(game_state=8)]))

    async def debug_cooldown(self):
        """ Disables cooldowns of unit abilities for the bot. Using it a second time disables it again. """
        await self._execute(debug=sc_pb.RequestDebug(debug=[debug_pb.DebugCommand(game_state=9)]))

    async def debug_tech_tree(self):
        """ Removes all tech requirements (e.g. can build a factory without having a barracks). Using it a second time disables it again. """
        await self._execute(debug=sc_pb.RequestDebug(debug=[debug_pb.DebugCommand(game_state=10)]))

    async def debug_upgrade(self):
        """ Researches all currently available upgrades. E.g. using it once unlocks combat shield, stimpack and 1-1. Using it a second time unlocks 2-2 and all other upgrades stay researched. """
        await self._execute(debug=sc_pb.RequestDebug(debug=[debug_pb.DebugCommand(game_state=11)]))

    async def debug_fast_build(self):
        """ Sets the build time of units and structures and upgrades to zero. Using it a second time disables it again. """
        await self._execute(debug=sc_pb.RequestDebug(debug=[debug_pb.DebugCommand(game_state=12)]))

    async def quick_save(self):
        """ Saves the current game state to an in-memory bookmark.
        See: https://github.com/Blizzard/s2client-proto/blob/eeaf5efaea2259d7b70247211dff98da0a2685a2/s2clientprotocol/sc2api.proto#L93 """
        await self._execute(quick_save=sc_pb.RequestQuickSave())

    async def quick_load(self):
        """ Loads the game state from the previously stored in-memory bookmark.
        Caution:
            - The SC2 Client will crash if the game wasn't quicksaved
            - The bot step iteration counter will not reset
            - self.state.game_loop will be set to zero after the quickload, and self.time is dependant on it """
        await self._execute(quick_load=sc_pb.RequestQuickLoad())
