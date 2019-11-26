import asyncio
import logging
import os.path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import json
import re
from typing import Any, List, Optional

import aiohttp
import portpicker

from .controller import Controller
from .paths import Paths
from sc2 import paths

from sc2.versions import VERSIONS

logger = logging.getLogger(__name__)


class kill_switch:
    _to_kill: List[Any] = []

    @classmethod
    def add(cls, value):
        logger.debug("kill_switch: Add switch")
        cls._to_kill.append(value)

    @classmethod
    def kill_all(cls):
        logger.info("kill_switch: Process cleanup")
        for p in cls._to_kill:
            p._clean()


class SC2Process:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        fullscreen: bool = False,
        render: bool = False,
        sc2_version: str = None,
        base_build: str = None,
        data_hash: str = None
    ) -> None:
        assert isinstance(host, str)
        assert isinstance(port, int) or port is None

        self._render = render
        self._fullscreen = fullscreen
        self._host = host
        if port is None:
            self._port = portpicker.pick_unused_port()
        else:
            self._port = port
        self._tmp_dir = tempfile.mkdtemp(prefix="SC2_")
        self._process = None
        self._session = None
        self._ws = None
        self._sc2_version = sc2_version
        self._base_build = base_build
        self._data_hash = data_hash


    async def __aenter__(self):
        kill_switch.add(self)

        def signal_handler(*args):
            # unused arguments: signal handling library expects all signal
            # callback handlers to accept two positional arguments
            kill_switch.kill_all()

        signal.signal(signal.SIGINT, signal_handler)

        try:
            self._process = self._launch()
            self._ws = await self._connect()
        except:
            await self._close_connection()
            self._clean()
            raise

        return Controller(self._ws, self)

    async def __aexit__(self, *args):
        kill_switch.kill_all()
        signal.signal(signal.SIGINT, signal.SIG_DFL)

    @property
    def ws_url(self):
        return f"ws://{self._host}:{self._port}/sc2api"

    @property
    def versions(self):
        """ Opens the versions.json file which origins from
        https://github.com/Blizzard/s2client-proto/blob/master/buildinfo/versions.json """
        return VERSIONS

    def find_data_hash(self, target_sc2_version: str):
        """ Returns the data hash from the matching version string. """
        version: dict
        for version in self.versions:
            if version["label"] == target_sc2_version:
                return version["data-hash"]

    def _launch(self):
        if self._base_build:
            executable = str(paths.latest_executeble(Paths.BASE / "Versions", self._base_build))
        else:
            executable = str(Paths.EXECUTABLE)
        args = paths.get_runner_args(Paths.CWD) + [
            executable,
            "-listen",
            self._host,
            "-port",
            str(self._port),
            "-displayMode",
            "1" if self._fullscreen else "0",
            "-dataDir",
            str(Paths.BASE),
            "-tempDir",
            self._tmp_dir,
        ]
        if self._sc2_version:

            def special_match(strg: str):
                """ Test if string contains only numbers and dots, which is a valid version string. """
                for version in self.versions:
                    if version["label"] == strg:
                        return True
                return False
            valid_version_string = special_match(self._sc2_version)
            if valid_version_string:
                self._data_hash = self.find_data_hash(self._sc2_version)
                assert (
                    self._data_hash is not None
                ), f"StarCraft 2 Client version ({self._sc2_version}) was not found inside sc2/versions.py file. Please check your spelling or check the versions.py file."

            else:
                logger.warning(
                    f'The submitted version string in sc2.rungame() function call (sc2_version="{self._sc2_version}") was not found in versions.py. Running latest version instead.'
                )

        if self._data_hash:
            args.extend(["-dataVersion", self._data_hash])

        if self._render:
            args.extend(["-eglpath", "libEGL.so"])

        if logger.getEffectiveLevel() <= logging.DEBUG:
            args.append("-verbose")

        return subprocess.Popen(
            args,
            cwd=(str(Paths.CWD) if Paths.CWD else None),
            # , env=run_config.env
        )

    async def _connect(self):
        for i in range(60):
            if self._process is None:
                # The ._clean() was called, clearing the process
                logger.debug("Process cleanup complete, exit")
                sys.exit()

            await asyncio.sleep(1)
            try:
                self._session = aiohttp.ClientSession()
                ws = await self._session.ws_connect(self.ws_url, timeout=120)
                # FIXME fix deprecation warning in for future aiohttp version
                # ws = await self._session.ws_connect(
                #     self.ws_url, timeout=aiohttp.client_ws.ClientWSTimeout(ws_close=120)
                # )
                logger.debug("Websocket connection ready")
                return ws
            except aiohttp.client_exceptions.ClientConnectorError:
                await self._session.close()
                if i > 15:
                    logger.debug("Connection refused (startup not complete (yet))")

        logger.debug("Websocket connection to SC2 process timed out")
        raise TimeoutError("Websocket")

    async def _close_connection(self):
        logger.info("Closing connection...")

        if self._ws is not None:
            await self._ws.close()

        if self._session is not None:
            await self._session.close()

    def _clean(self):
        logger.info("Cleaning up...")

        if self._process is not None:
            if self._process.poll() is None:
                for _ in range(3):
                    self._process.terminate()
                    time.sleep(0.5)
                    if not self._process or self._process.poll() is not None:
                        break
                else:
                    self._process.kill()
                    self._process.wait()
                    logger.error("KILLED")

        if os.path.exists(self._tmp_dir):
            shutil.rmtree(self._tmp_dir)

        self._process = None
        self._ws = None
        logger.info("Cleanup complete")
