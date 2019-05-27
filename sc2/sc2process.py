import asyncio
import logging
import os.path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from typing import Any, List, Optional

import aiohttp
import portpicker

from .controller import Controller
from .paths import Paths

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
        self, host: str = "127.0.0.1", port: Optional[int] = None, fullscreen: bool = False, render: bool = False
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

    def _launch(self):
        args = [
            str(Paths.EXECUTABLE),
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
                    if self._process.poll() is not None:
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
