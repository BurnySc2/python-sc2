import asyncio
from aiohttp import web, WSMsgType, WSMessage
import logging
import os
import platform
import subprocess
import time
import traceback

from s2clientprotocol import sc2api_pb2 as sc_pb

from .controller import Controller
from .data import Result, Status
from .player import BotProcess

from pathlib import Path

logger = logging.getLogger(__name__)


class Proxy:
    def __init__(self, controller: Controller, player: BotProcess, proxyport: int):
        self.ctrler = controller
        self.player = player
        self.port = proxyport

        self.result = None
        self.player_id: int = None
        self.done = False

    async def parse_request(self, msg):
        request = sc_pb.Request()
        request.ParseFromString(msg.data)
        if request.HasField("quit"):
            request = sc_pb.Request(leave_game=sc_pb.RequestLeaveGame())
        if request.HasField("leave_game"):
            logger.info(f"Proxy: player {self.player.name}({self.player_id}) surrenders")
            self.result = {self.player_id: Result.Defeat}
        elif request.HasField("join_game") and not request.join_game.HasField("player_name"):
            request.join_game.player_name = self.player.name
        await self.ctrler._ws.send_bytes(request.SerializeToString())

    async def get_response(self):
        response_bytes = None
        try:
            response_bytes = await self.ctrler._ws.receive_bytes()
        except TypeError as e:
            logger.exception("Cannot receive: SC2 Connection already closed.")
            tb = traceback.format_exc()
            logger.error(f"Exception {e}: {tb}")
        except asyncio.CancelledError:
            print(f"Proxy({self.player.name}), caught receive from sc2, {traceback.format_exc()}")
            try:
                x = await self.ctrler._ws.receive_bytes()
                if response_bytes is None:
                    response_bytes = x
            except (
                    asyncio.CancelledError,
                    asyncio.TimeoutError,
                    Exception
            ) as e:
                tb = traceback.format_exc()
                logger.error(f"Exception {e}: {tb}")
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Exception {e}: {tb}")
        return response_bytes

    async def parse_response(self, response_bytes):
        response = sc_pb.Response()
        response.ParseFromString(response_bytes)
        new_status = Status(response.status)
        if new_status != self.ctrler._status:
            logger.info(f"Controller({self.player.name}): {self.ctrler._status}->{new_status}")
            self.ctrler._status = new_status
        if self.player_id is None:
            if response.HasField("join_game"):
                self.player_id = response.join_game.player_id
                print(f"Proxy({self.player.name}): got join_game for {self.player_id}")
        if self.result is None:
            if response.HasField("observation") and response.observation.player_result:
                self.result = {pr.player_id: Result(pr.result) for pr in response.observation.player_result}

    async def proxy_handler(self, request):
        bot_ws = web.WebSocketResponse(receive_timeout=30)
        await bot_ws.prepare(request)
        try:
            async for msg in bot_ws:
                if msg.data is None:
                    raise TypeError(f"data is None, {msg}")
                if msg.data and msg.type == WSMsgType.BINARY:

                    await self.parse_request(msg)

                    response_bytes = await self.get_response()
                    if response_bytes is None:
                        raise ConnectionError("Could not get response_bytes")

                    await self.parse_response(response_bytes)
                    await bot_ws.send_bytes(response_bytes)

                elif msg.type == WSMsgType.CLOSED:
                    logger.error("Client shutdown")
                else:
                    logger.error("Incorrect message type")
        except Exception as e:
            IGNORED_ERRORS = {ConnectionError, asyncio.CancelledError}
            if not any([isinstance(e, E) for E in IGNORED_ERRORS]):
                tb = traceback.format_exc()
                print(f"Proxy({self.player.name}): Caught {e} traceback: {tb}")
        finally:
            try:
                if self.ctrler._status in {Status.in_game, Status.in_replay}:
                    await self.ctrler._execute(leave_game=sc_pb.RequestLeaveGame())
                await bot_ws.close()
            except Exception as ee:
                tbb = traceback.format_exc()
                print(f"Proxy({self.player.name}): Caught during Surrender", ee, "traceback:", tbb)
            self.done = True
        return bot_ws

    async def play_with_proxy(self, startport):
        print(f"Proxy({self.port}): starting app")
        app = web.Application()
        app.router.add_route("GET", "/sc2api", self.proxy_handler)
        apprunner = web.AppRunner(app, access_log=None)
        await apprunner.setup()
        appsite = web.TCPSite(apprunner, self.ctrler._process._host, self.port)
        await appsite.start()

        subproc_args = {"cwd": str(self.player.path),
                        "stderr": subprocess.STDOUT}
        if platform.system() == "Linux":
            subproc_args["preexec_fn"] = os.setpgrp
        elif platform.system() == "Windows":
            subproc_args["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        if self.player.stdout is not None:
            with open(self.player.stdout, "w+") as out:
                bot_process = subprocess.Popen(
                    self.player.cmd_line(self.port, startport, self.ctrler._process._host), stdout=out, **subproc_args)
        else:
            # outfile = os.path.join(self.player.launch_str, "data", "stderr.txt")
            # with open(outfile, "w+") as out:
            #     bot_process = subprocess.Popen(
            #         self.player.cmd_line(self.port, startport, self.ctrler._process._host), stdout=out, **subproc_args)
            bot_process = subprocess.Popen(
                self.player.cmd_line(self.port, startport, self.ctrler._process._host), stdout=subprocess.PIPE, **subproc_args)

        print(f"Proxy({self.port}): starting while loop")
        while self.result is None:
            bot_alive = bot_process and bot_process.poll() is None
            sc2_alive = self.ctrler.running and self.ctrler._process._process.poll() is None
            if self.done or not (bot_alive and sc2_alive):
                logger.info(f"Proxy({self.port}): {self.player.name} died/rekt'ed, "
                      f"bot{(not bot_alive) * ' not'} alive, sc2{(not sc2_alive) * ' not'} alive")
                if sc2_alive and not self.done:
                    try:
                        res = await self.ctrler.ping()
                        if res.status in {Status.in_game, Status.in_replay, Status.ended}:
                            res = await self.ctrler._execute(observation=sc_pb.RequestObservation())
                            if res.HasField("observation") and res.observation.player_result:
                                self.result = {pr.player_id: Result(pr.result) for pr in res.observation.player_result}
                    except Exception as e:
                        tb = traceback.format_exc()
                        logger.error(f"Obs-check: {e}, traceback: {tb}")
                logger.info(f"Proxy({self.port}): breaking, result {self.result}")
                break
            await asyncio.sleep(5)

        # cleanup
        logger.info(f"({self.port}): cleaning up bot")
        for i in range(3):
            if isinstance(bot_process, subprocess.Popen):
                if bot_process.stdout and not bot_process.stdout.closed:
                    # print("==================output for player", self.player.name)
                    # print(*bot_process.stdout.readlines())
                    bot_process.stdout.close()
                    # print("==================")
                bot_process.terminate()
                bot_process.wait()
            time.sleep(0.5)
            if not bot_process or bot_process.poll() is not None:
                break
        else:
            bot_process.terminate()
            bot_process.wait()
        try:
            await apprunner.cleanup()
        except Exception as e:
            logger.error(f"cleaning error {e}")
        if isinstance(self.result, dict):
            self.result[None] = None
            return self.result[self.player_id]
        else:
            return self.result

