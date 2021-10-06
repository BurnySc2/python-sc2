import asyncio
import json
import os
import platform
import signal
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Union

import async_timeout
import mpyq
import portpicker
import six
from aiohttp import ClientSession, ClientWebSocketResponse
from loguru import logger
from s2clientprotocol import sc2api_pb2 as sc_pb

from sc2.client import Client
from sc2.controller import Controller
from sc2.data import CreateGameError, Result, Status
from sc2.game_state import GameState
from sc2.maps import Map
from sc2.player import AbstractPlayer, Bot, BotProcess, Human
from sc2.portconfig import Portconfig
from sc2.protocol import ConnectionAlreadyClosed, ProtocolError
from sc2.proxy import Proxy
from sc2.sc2process import SC2Process, kill_switch

# Set the global logging level
logger.remove()
logger.add(sys.stdout, level="INFO")


@dataclass
class GameMatch:
    """Dataclass for hosting a match of SC2.
    This contains all of the needed information for RequestCreateGame.
    :param sc2_config: dicts of arguments to unpack into sc2process's construction, one per player
        second sc2_config will be ignored if only one sc2_instance is spawned
        e.g. sc2_args=[{"fullscreen": True}, {}]: only player 1's sc2instance will be fullscreen
    :param game_time_limit: The time (in seconds) until a match is artificially declared a Tie
    """

    map_sc2: Map
    players: List[AbstractPlayer]
    realtime: bool = False
    random_seed: int = None
    disable_fog: bool = None
    sc2_config: List[Dict] = None
    game_time_limit: int = None

    def __post_init__(self):
        # avoid players sharing names
        if len(self.players) > 1 and self.players[0].name is not None and self.players[0].name == self.players[1].name:
            self.players[1].name += "2"

        if self.sc2_config is not None:
            if isinstance(self.sc2_config, dict):
                self.sc2_config = [self.sc2_config]
            if len(self.sc2_config) == 0:
                self.sc2_config = [{}]
            while len(self.sc2_config) < len(self.players):
                self.sc2_config += self.sc2_config
            self.sc2_config = self.sc2_config[:len(self.players)]

    @property
    def needed_sc2_count(self) -> int:
        return sum(player.needs_sc2 for player in self.players)

    @property
    def host_game_kwargs(self) -> Dict:
        return {
            "map_settings": self.map_sc2,
            "players": self.players,
            "realtime": self.realtime,
            "random_seed": self.random_seed,
            "disable_fog": self.disable_fog,
        }

    def __repr__(self):
        p1 = self.players[0]
        p1 = p1.name if p1.name else p1
        p2 = self.players[1]
        p2 = p2.name if p2.name else p2
        return f"Map: {self.map_sc2.name}, {p1} vs {p2}, realtime:{self.realtime}, seed={self.random_seed}"


class SlidingTimeWindow:
    def __init__(self, size: int):
        assert size > 0

        self.window_size = size
        self.window = []

    def push(self, value: float):
        self.window = (self.window + [value])[-self.window_size:]

    def clear(self):
        self.window = []

    @property
    def sum(self) -> float:
        return sum(self.window)

    @property
    def available(self) -> float:
        return sum(self.window[1:])

    @property
    def available_fmt(self) -> float:
        return ",".join(f"{w:.2f}" for w in self.window[1:])


async def _play_game_human(client, player_id, realtime, game_time_limit):
    while True:
        state = await client.observation()
        if client._game_result:
            return client._game_result[player_id]

        if game_time_limit and (state.observation.observation.game_loop * 0.725 * (1 / 16)) > game_time_limit:
            print(state.observation.game_loop, state.observation.game_loop * 0.14)
            return Result.Tie

        if not realtime:
            await client.step()


async def _play_game_ai(client, player_id, ai, realtime, step_time_limit, game_time_limit):
    if realtime:
        assert step_time_limit is None

    # step_time_limit works like this:
    # * If None, then step time is not limited
    # * If given integer or float, the bot will simpy resign if any step takes longer than that
    # * Otherwise step_time_limit must be an object, with following settings:
    #
    # Key         | Value      | Description
    # ------------|------------|-------------
    # penalty     | None       | No penalty, the bot can continue on next step
    # penalty     | N: int     | Cooldown penalty, BotAI.on_step will not be called for N steps
    # penalty     | "resign"   | Bot resigns when going over time limit
    # time_limit  | int/float  | Time limit for a single step
    # window_size | N: int     | The time limit will be used for last N steps, instad of 1
    #
    # Cooldown is a harsh penalty. The both loses the ability to act, but even worse,
    # the observation data from skipped steps is also lost. It's like falling asleep in
    # a middle of the game.
    time_penalty_cooldown = 0
    if step_time_limit is None:
        time_limit = None
        time_window = None
        time_penalty = None
    elif isinstance(step_time_limit, (int, float)):
        time_limit = float(step_time_limit)
        time_window = SlidingTimeWindow(1)
        time_penalty = "resign"
    else:
        assert isinstance(step_time_limit, dict)
        time_penalty = step_time_limit.get("penalty", None)
        time_window = SlidingTimeWindow(int(step_time_limit.get("window_size", 1)))
        time_limit = float(step_time_limit.get("time_limit", None))

    ai._initialize_variables()

    game_data = await client.get_game_data()
    game_info = await client.get_game_info()
    ping_response = await client.ping()

    # This game_data will become self._game_data in botAI
    ai._prepare_start(
        client, player_id, game_info, game_data, realtime=realtime, base_build=ping_response.ping.base_build
    )
    state = await client.observation()
    # check game result every time we get the observation
    if client._game_result:
        await ai.on_end(client._game_result[player_id])
        return client._game_result[player_id]
    gs = GameState(state.observation)
    proto_game_info = await client._execute(game_info=sc_pb.RequestGameInfo())
    try:
        ai._prepare_step(gs, proto_game_info)
        await ai.on_before_start()
        ai._prepare_first_step()
        await ai.on_start()
    except Exception as e:
        logger.exception(f"AI on_start threw an error")
        logger.error(f"resigning due to previous error")
        await ai.on_end(Result.Defeat)
        return Result.Defeat

    iteration = 0
    # Only used in realtime=True
    previous_state_observation = None
    while True:
        if iteration != 0:
            if realtime:
                # On realtime=True, might get an error here: sc2.protocol.ProtocolError: ['Not in a game']
                try:
                    requested_step = gs.game_loop + client.game_step
                    state = await client.observation(requested_step)
                    # If the bot took too long in the previous observation, request another observation one frame after
                    if state.observation.observation.game_loop > requested_step:
                        logger.debug(f"Skipped a step in realtime=True")
                        previous_state_observation = state.observation
                        state = await client.observation(state.observation.observation.game_loop + 1)
                except ProtocolError:
                    pass
            else:
                state = await client.observation()
            # check game result every time we get the observation
            if client._game_result:
                try:
                    await ai.on_end(client._game_result[player_id])
                except TypeError as error:
                    # print(f"caught type error {error}")
                    # print(f"return {client._game_result[player_id]}")
                    return client._game_result[player_id]
                return client._game_result[player_id]
            gs = GameState(state.observation, previous_state_observation)
            previous_state_observation = None
            logger.debug(f"Score: {gs.score.score}")

            if game_time_limit and (gs.game_loop * 0.725 * (1 / 16)) > game_time_limit:
                await ai.on_end(Result.Tie)
                return Result.Tie
            proto_game_info = await client._execute(game_info=sc_pb.RequestGameInfo())
            ai._prepare_step(gs, proto_game_info)

        logger.debug(f"Running AI step, it={iteration} {gs.game_loop * 0.725 * (1 / 16):.2f}s")

        try:
            if realtime:
                # Issue event like unit created or unit destroyed
                await ai.issue_events()
                await ai.on_step(iteration)
                await ai._after_step()
            else:
                if time_penalty_cooldown > 0:
                    time_penalty_cooldown -= 1
                    logger.warning(f"Running AI step: penalty cooldown: {time_penalty_cooldown}")
                    iteration -= 1  # Do not increment the iteration on this round
                elif time_limit is None:
                    # Issue event like unit created or unit destroyed
                    await ai.issue_events()
                    await ai.on_step(iteration)
                    await ai._after_step()
                else:
                    out_of_budget = False
                    budget = time_limit - time_window.available

                    # Tell the bot how much time it has left attribute
                    ai.time_budget_available = budget

                    if budget < 0:
                        logger.warning(f"Running AI step: out of budget before step")
                        step_time = 0.0
                        out_of_budget = True
                    else:
                        step_start = time.monotonic()
                        try:
                            async with async_timeout.timeout(budget):
                                await ai.issue_events()
                                await ai.on_step(iteration)
                        except asyncio.TimeoutError:
                            step_time = time.monotonic() - step_start
                            logger.warning(
                                f"Running AI step: out of budget; " +
                                f"budget={budget:.2f}, steptime={step_time:.2f}, " +
                                f"window={time_window.available_fmt}"
                            )
                            out_of_budget = True
                        step_time = time.monotonic() - step_start

                    time_window.push(step_time)

                    if out_of_budget and time_penalty is not None:
                        if time_penalty == "resign":
                            raise RuntimeError("Out of time")
                        else:
                            time_penalty_cooldown = int(time_penalty)
                            time_window.clear()

                    await ai._after_step()
        except Exception as e:
            if isinstance(e, ProtocolError) and e.is_game_over_error:
                if realtime:
                    return None
                result = client._game_result[player_id]
                if result is None:
                    logger.error("Game over, but no results gathered")
                    raise
                await ai.on_end(result)
                return result
            # NOTE: this message is caught by pytest suite
            logger.exception(f"AI step threw an error")  # DO NOT EDIT!
            logger.error(f"Error: {e}")
            logger.error(f"Resigning due to previous error")
            try:
                await ai.on_end(Result.Defeat)
            except TypeError as error:
                # print(f"caught type error {error}")
                # print(f"return {Result.Defeat}")
                return Result.Defeat
            return Result.Defeat

        logger.debug(f"Running AI step: done")

        if not realtime:
            if not client.in_game:  # Client left (resigned) the game
                await ai.on_end(client._game_result[player_id])
                return client._game_result[player_id]

            await client.step()

        iteration += 1


async def _play_game(
    player,
    client: Client,
    realtime,
    portconfig,
    step_time_limit=None,
    game_time_limit=None,
    rgb_render_config=None
) -> Result:
    assert isinstance(realtime, bool), repr(realtime)

    player_id = await client.join_game(
        player.name, player.race, portconfig=portconfig, rgb_render_config=rgb_render_config
    )
    logger.info(f"Player {player_id} - {player.name if player.name else str(player)}")

    if isinstance(player, Human):
        result = await _play_game_human(client, player_id, realtime, game_time_limit)
    else:
        result = await _play_game_ai(client, player_id, player.ai, realtime, step_time_limit, game_time_limit)

    logger.info(
        f"Result for player {player_id} - {player.name if player.name else str(player)}: "
        f"{result._name_ if isinstance(result, Result) else result}"
    )

    return result


async def _play_replay(client, ai, realtime=False, player_id=0):
    ai._initialize_variables()

    game_data = await client.get_game_data()
    game_info = await client.get_game_info()
    ping_response = await client.ping()

    client.game_step = 1
    # This game_data will become self._game_data in botAI
    ai._prepare_start(
        client, player_id, game_info, game_data, realtime=realtime, base_build=ping_response.ping.base_build
    )
    state = await client.observation()
    # Check game result every time we get the observation
    if client._game_result:
        await ai.on_end(client._game_result[player_id])
        return client._game_result[player_id]
    gs = GameState(state.observation)
    proto_game_info = await client._execute(game_info=sc_pb.RequestGameInfo())
    ai._prepare_step(gs, proto_game_info)
    ai._prepare_first_step()
    try:
        await ai.on_start()
    except Exception as e:
        logger.exception(f"AI on_start threw an error")
        logger.error(f"resigning due to previous error")
        await ai.on_end(Result.Defeat)
        return Result.Defeat

    iteration = 0
    while True:
        if iteration != 0:
            if realtime:
                # TODO: check what happens if a bot takes too long to respond, so that the requested
                #  game_loop might already be in the past
                state = await client.observation(gs.game_loop + client.game_step)
            else:
                state = await client.observation()
            # check game result every time we get the observation
            if client._game_result:
                try:
                    await ai.on_end(client._game_result[player_id])
                except TypeError as error:
                    # print(f"caught type error {error}")
                    # print(f"return {client._game_result[player_id]}")
                    return client._game_result[player_id]
                return client._game_result[player_id]
            gs = GameState(state.observation)
            logger.debug(f"Score: {gs.score.score}")

            proto_game_info = await client._execute(game_info=sc_pb.RequestGameInfo())
            ai._prepare_step(gs, proto_game_info)

        logger.debug(f"Running AI step, it={iteration} {gs.game_loop * 0.725 * (1 / 16):.2f}s")

        try:
            # Issue event like unit created or unit destroyed
            await ai.issue_events()
            await ai.on_step(iteration)
            await ai._after_step()

        except Exception as e:
            if isinstance(e, ProtocolError) and e.is_game_over_error:
                if realtime:
                    return None
                # result = client._game_result[player_id]
                # if result is None:
                #     logger.error("Game over, but no results gathered")
                #     raise
                await ai.on_end(Result.Victory)
                return None
            # NOTE: this message is caught by pytest suite
            logger.exception(f"AI step threw an error")  # DO NOT EDIT!
            logger.error(f"Error: {e}")
            logger.error(f"Resigning due to previous error")
            try:
                await ai.on_end(Result.Defeat)
            except TypeError as error:
                # print(f"caught type error {error}")
                # print(f"return {Result.Defeat}")
                return Result.Defeat
            return Result.Defeat

        logger.debug(f"Running AI step: done")

        if not realtime:
            if not client.in_game:  # Client left (resigned) the game
                await ai.on_end(Result.Victory)
                return Result.Victory

        await client.step()  # unindent one line to work in realtime

        iteration += 1


async def _setup_host_game(server: Controller, map_settings, players, realtime, random_seed=None, disable_fog=None):
    r = await server.create_game(map_settings, players, realtime, random_seed, disable_fog)
    if r.create_game.HasField("error"):
        err = f"Could not create game: {CreateGameError(r.create_game.error)}"
        if r.create_game.HasField("error_details"):
            err += f": {r.create_game.error_details}"
        logger.critical(err)
        raise RuntimeError(err)

    return Client(server._ws)


async def _host_game(
    map_settings,
    players,
    realtime=False,
    portconfig=None,
    save_replay_as=None,
    step_time_limit=None,
    game_time_limit=None,
    rgb_render_config=None,
    random_seed=None,
    sc2_version=None,
    disable_fog=None,
):

    assert players, "Can't create a game without players"

    assert any(isinstance(p, (Human, Bot)) for p in players)

    async with SC2Process(
        fullscreen=players[0].fullscreen, render=rgb_render_config is not None, sc2_version=sc2_version
    ) as server:
        await server.ping()

        client = await _setup_host_game(server, map_settings, players, realtime, random_seed, disable_fog)
        # Bot can decide if it wants to launch with 'raw_affects_selection=True'
        if not isinstance(players[0], Human) and getattr(players[0].ai, "raw_affects_selection", None) is not None:
            client.raw_affects_selection = players[0].ai.raw_affects_selection

        try:
            result = await _play_game(
                players[0], client, realtime, portconfig, step_time_limit, game_time_limit, rgb_render_config
            )
            if save_replay_as is not None:
                await client.save_replay(save_replay_as)
            await client.leave()
            await client.quit()
        except ConnectionAlreadyClosed:
            logger.error(f"Connection was closed before the game ended")
            return None

        return result


async def _host_game_aiter(
    map_settings,
    players,
    realtime,
    portconfig=None,
    save_replay_as=None,
    step_time_limit=None,
    game_time_limit=None,
):
    assert players, "Can't create a game without players"

    assert any(isinstance(p, (Human, Bot)) for p in players)

    async with SC2Process() as server:
        while True:
            await server.ping()

            client = await _setup_host_game(server, map_settings, players, realtime)
            if not isinstance(players[0], Human) and getattr(players[0].ai, "raw_affects_selection", None) is not None:
                client.raw_affects_selection = players[0].ai.raw_affects_selection

            try:
                result = await _play_game(players[0], client, realtime, portconfig, step_time_limit, game_time_limit)

                if save_replay_as is not None:
                    await client.save_replay(save_replay_as)
                await client.leave()
            except ConnectionAlreadyClosed:
                logger.error(f"Connection was closed before the game ended")
                return

            new_players = yield result
            if new_players is not None:
                players = new_players


def _host_game_iter(*args, **kwargs):
    game = _host_game_aiter(*args, **kwargs)
    new_playerconfig = None
    while True:
        new_playerconfig = yield asyncio.get_event_loop().run_until_complete(game.asend(new_playerconfig))


async def _join_game(
    players,
    realtime,
    portconfig,
    save_replay_as=None,
    step_time_limit=None,
    game_time_limit=None,
):
    async with SC2Process(fullscreen=players[1].fullscreen) as server:
        await server.ping()

        client = Client(server._ws)
        # Bot can decide if it wants to launch with 'raw_affects_selection=True'
        if not isinstance(players[1], Human) and getattr(players[1].ai, "raw_affects_selection", None) is not None:
            client.raw_affects_selection = players[1].ai.raw_affects_selection

        try:
            result = await _play_game(players[1], client, realtime, portconfig, step_time_limit, game_time_limit)
            if save_replay_as is not None:
                await client.save_replay(save_replay_as)
            await client.leave()
            await client.quit()
        except ConnectionAlreadyClosed:
            logger.error(f"Connection was closed before the game ended")
            return None

        return result


async def _setup_replay(server, replay_path, realtime, observed_id):
    await server.start_replay(replay_path, realtime, observed_id)
    return Client(server._ws)


async def _host_replay(replay_path, ai, realtime, portconfig, base_build, data_version, observed_id):
    async with SC2Process(fullscreen=False, base_build=base_build, data_hash=data_version) as server:
        response = await server.ping()

        client = await _setup_replay(server, replay_path, realtime, observed_id)
        result = await _play_replay(client, ai, realtime)
        return result


def get_replay_version(replay_path):
    with open(replay_path, "rb") as f:
        replay_data = f.read()
        replay_io = six.BytesIO()
        replay_io.write(replay_data)
        replay_io.seek(0)
        archive = mpyq.MPQArchive(replay_io).extract()
        metadata = json.loads(archive[b"replay.gamemetadata.json"].decode("utf-8"))
        return metadata["BaseBuild"], metadata["DataVersion"]


def run_game(map_settings, players, **kwargs):
    if sum(isinstance(p, (Human, Bot)) for p in players) > 1:
        host_only_args = ["save_replay_as", "rgb_render_config", "random_seed", "sc2_version", "disable_fog"]
        join_kwargs = {k: v for k, v in kwargs.items() if k not in host_only_args}

        portconfig = Portconfig()
        result = asyncio.get_event_loop().run_until_complete(
            asyncio.gather(
                _host_game(map_settings, players, **kwargs, portconfig=portconfig),
                _join_game(players, **join_kwargs, portconfig=portconfig),
            )
        )
    else:
        result = asyncio.get_event_loop().run_until_complete(_host_game(map_settings, players, **kwargs))
    return result


def run_replay(ai, replay_path, realtime=False, observed_id=0):
    portconfig = Portconfig()
    assert os.path.isfile(replay_path), f"Replay does not exist at the given path: {replay_path}"
    assert os.path.isabs(
        replay_path
    ), f'Replay path has to be an absolute path, e.g. "C:/replays/my_replay.SC2Replay" but given path was "{replay_path}"'
    base_build, data_version = get_replay_version(replay_path)
    result = asyncio.get_event_loop().run_until_complete(
        _host_replay(replay_path, ai, realtime, portconfig, base_build, data_version, observed_id)
    )
    return result


async def play_from_websocket(
    ws_connection: Union[str, ClientWebSocketResponse],
    player: AbstractPlayer,
    realtime: bool = False,
    portconfig: Portconfig = None,
    save_replay_as=None,
    game_time_limit: int = None,
    should_close=True,
):
    """Use this to play when the match is handled externally e.g. for bot ladder games.
    Portconfig MUST be specified if not playing vs Computer.
    :param ws_connection: either a string("ws://{address}:{port}/sc2api") or a ClientWebSocketResponse object
    :param should_close: closes the connection if True. Use False if something else will reuse the connection

    e.g. ladder usage: play_from_websocket("ws://127.0.0.1:5162/sc2api", MyBot, False, portconfig=my_PC)
    """
    session = None
    try:
        if isinstance(ws_connection, str):
            session = ClientSession()
            ws_connection = await session.ws_connect(ws_connection, timeout=120)
            should_close = True
        client = Client(ws_connection)
        result = await _play_game(player, client, realtime, portconfig, game_time_limit=game_time_limit)
        if save_replay_as is not None:
            await client.save_replay(save_replay_as)
    except ConnectionAlreadyClosed:
        logger.error(f"Connection was closed before the game ended")
        return None
    finally:
        if should_close:
            await ws_connection.close()
            if session:
                await session.close()

    return result


async def run_match(controllers: List[Controller], match: GameMatch, close_ws=True):
    await _setup_host_game(controllers[0], **match.host_game_kwargs)

    # Setup portconfig beforehand, so all players use the same ports
    startport = None
    portconfig = None
    if match.needed_sc2_count > 1:
        if any(isinstance(player, BotProcess) for player in match.players):
            portconfig = Portconfig.contiguous_ports()
            # Most ladder bots generate their server and client ports as [s+2, s+3], [s+4, s+5]
            startport = portconfig.server[0] - 2
        else:
            portconfig = Portconfig()

    proxies = []
    coros = []
    i = 0
    for player in match.players:
        if player.needs_sc2:
            if isinstance(player, BotProcess):
                pport = portpicker.pick_unused_port()
                p = Proxy(controllers[i], player, pport, match.game_time_limit, match.realtime)
                proxies.append(p)
                coros.append(p.play_with_proxy(startport))
            else:
                coros.append(
                    play_from_websocket(
                        controllers[i]._ws,
                        player,
                        match.realtime,
                        portconfig,
                        should_close=close_ws,
                        game_time_limit=match.game_time_limit,
                    )
                )
            i += 1

    # async_results = await asyncio.wait_for(asyncio.gather(*coros, return_exceptions=True), timeout=None)
    async_results = await asyncio.gather(*coros, return_exceptions=True)

    if not isinstance(async_results, list):
        async_results = [async_results]
    for i, a in enumerate(async_results):
        if isinstance(a, Exception):
            logger.error(f"Exception[{a}] thrown by {[p for p in match.players if p.needs_sc2][i]}")

    return process_results(match.players, async_results)


def process_results(players, async_results):
    opp_res = {Result.Victory: Result.Defeat, Result.Defeat: Result.Victory, Result.Tie: Result.Tie}
    result: Dict[AbstractPlayer, Result] = {}
    i = 0
    for player in players:
        if player.needs_sc2:
            if sum(r == Result.Victory for r in async_results) <= 1:
                result[player] = async_results[i]
            else:
                result[player] = Result.Undecided
            i += 1
        else:  # computer
            other_result = async_results[0]
            result[player] = opp_res[other_result] if other_result in opp_res else None

    return result


async def maintain_SCII_count(count: int, controllers: List[Controller], proc_args: List[Dict] = None):
    """Modifies the given list of controllers to reflect the desired amount of SCII processes"""
    # kill unhealthy ones.
    if controllers:
        toRemove = []
        alive = await asyncio.wait_for(
            asyncio.gather(*(c.ping() for c in controllers if not c._ws.closed), return_exceptions=True), timeout=20
        )
        i = 0  # for alive
        for controller in controllers:
            if controller._ws.closed:
                if not controller._process._session.closed:
                    await controller._process._session.close()
                toRemove.append(controller)
            else:
                if not isinstance(alive[i], sc_pb.Response):
                    try:
                        await controller._process._close_connection()
                    finally:
                        toRemove.append(controller)
                i += 1
        for c in toRemove:
            c._process._clean()
            if c._process in kill_switch._to_kill:
                kill_switch._to_kill.remove(c._process)
            controllers.remove(c)

    # spawn more
    if len(controllers) < count:
        needed = count - len(controllers)
        if proc_args:
            index = len(controllers) % len(proc_args)
        else:
            proc_args = [{} for _ in range(needed)]
            index = 0
        extra = [SC2Process(**proc_args[(index + _) % len(proc_args)]) for _ in range(needed)]
        logger.info(f"Creating {needed} more SC2 Processes")
        for k in range(3):  # try thrice
            if platform.system() == "Linux":
                # Works on linux: start one client after the other
                new_controllers = [await asyncio.wait_for(sc.__aenter__(), timeout=50) for sc in extra]
            else:
                # Doesnt seem to work on linux: starting 2 clients nearly at the same time
                new_controllers = await asyncio.wait_for(
                    asyncio.gather(*[sc.__aenter__() for sc in extra], return_exceptions=True), timeout=50
                )

            controllers.extend(c for c in new_controllers if isinstance(c, Controller))
            if len(controllers) == count:
                await asyncio.wait_for(asyncio.gather(*(c.ping() for c in controllers)), timeout=20)
                break
            extra = [
                extra[i] for i, result in enumerate(new_controllers) if not isinstance(new_controllers, Controller)
            ]
        else:
            logger.critical("Could not launch sufficient SC2")
            raise RuntimeError

    # kill excess
    while len(controllers) > count:
        proc = controllers.pop()
        proc = proc._process
        logger.info(f"Removing SCII listening to {proc._port}")
        await proc._close_connection()
        proc._clean()
        if proc in kill_switch._to_kill:
            kill_switch._to_kill.remove(proc)


def run_multiple_games(matches: List[GameMatch]):
    return asyncio.get_event_loop().run_until_complete(a_run_multiple_games(matches))


async def a_run_multiple_games(matches: List[GameMatch]):
    """Run multiple matches.
    Non-python bots are supported.
    When playing bot vs bot, this is less likely to fatally crash than repeating run_game()
    """
    if not matches:
        return

    results = []
    controllers = []
    for m in matches:
        result = None
        dont_restart = m.needed_sc2_count == 2
        try:
            await maintain_SCII_count(m.needed_sc2_count, controllers, m.sc2_config)
            result = await run_match(controllers, m, close_ws=dont_restart)
        except SystemExit as e:
            logger.info(f"Game exit'ed as {e} during match {m}")
        except Exception as e:
            logger.info(f"Exception {e} thrown in match {m}")
        finally:
            if dont_restart:  # Keeping them alive after a non-computer match can cause crashes
                await maintain_SCII_count(0, controllers, m.sc2_config)
            results.append(result)
    kill_switch.kill_all()
    return results


async def a_run_multiple_games_nokill(matches: List[GameMatch]):
    """Run multiple matches while reusing SCII processes.
    Prone to crashes and stalls
    """
    # FIXME: check whether crashes between bot-vs-bot are avoidable or not
    if not matches:
        return

    # Start the matches
    results = []
    controllers = []
    for m in matches:
        logger.info(f"Starting match {1 + len(results)}: {m}")
        result = None
        try:
            await maintain_SCII_count(m.needed_sc2_count, controllers, m.sc2_config)
            result = await run_match(controllers, m, close_ws=False)
        except SystemExit as e:
            logger.critical(f"Game sys.exit'ed as {e} during match {m}")
        except Exception as e:
            logger.trace(f"Exception {e} thrown in match {m}")
        finally:
            for c in controllers:
                try:
                    await c.ping()
                    if c._status != Status.launched:
                        await c._execute(leave_game=sc_pb.RequestLeaveGame())
                except Exception as e:
                    if not (isinstance(e, ProtocolError) and e.is_game_over_error):
                        logger.info(f"controller {c.__dict__} threw {e}")

            results.append(result)

    # Fire the killswitch manually, instead of letting the winning player fire it.
    await asyncio.wait_for(asyncio.gather(*(c._process._close_connection() for c in controllers)), timeout=50)
    kill_switch.kill_all()
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    return results
