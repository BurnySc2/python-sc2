import asyncio

import logging
import sys

from s2clientprotocol import sc2api_pb2 as sc_pb

from .data import Status

logger = logging.getLogger(__name__)


class ProtocolError(Exception):
    @property
    def is_game_over_error(self) -> bool:
        return self.args[0] in ["['Game has already ended']", "['Not supported if game has already ended']"]


class ConnectionAlreadyClosed(ProtocolError):
    pass


class Protocol:
    def __init__(self, ws):
        """
        :param ws:
        """
        assert ws
        self._ws = ws
        self._status = None

    async def __request(self, request):
        logger.debug(f"Sending request: {request !r}")
        try:
            await self._ws.send_bytes(request.SerializeToString())
        except TypeError:
            logger.exception("Cannot send: Connection already closed.")
            raise ConnectionAlreadyClosed("Connection already closed.")
        logger.debug(f"Request sent")

        response = sc_pb.Response()
        try:
            response_bytes = await self._ws.receive_bytes()
        except TypeError:
            # logger.exception("Cannot receive: Connection already closed.")
            # raise ConnectionAlreadyClosed("Connection already closed.")
            logger.info("Cannot receive: Connection already closed.")
            sys.exit(2)
        except asyncio.CancelledError:
            # If request is sent, the response must be received before reraising cancel
            try:
                await self._ws.receive_bytes()
            except asyncio.CancelledError:
                logger.critical("Requests must not be cancelled multiple times")
                sys.exit(2)
            raise

        response.ParseFromString(response_bytes)
        logger.debug(f"Response received")
        return response

    async def _execute(self, **kwargs):
        assert len(kwargs) == 1, "Only one request allowed"

        request = sc_pb.Request(**kwargs)

        response = await self.__request(request)

        new_status = Status(response.status)
        if new_status != self._status:
            logger.info(f"Client status changed to {new_status} (was {self._status})")
        self._status = new_status

        if response.error:
            logger.debug(f"Response contained an error: {response.error}")
            raise ProtocolError(f"{response.error}")

        return response

    async def ping(self):
        result = await self._execute(ping=sc_pb.RequestPing())
        return result

    async def quit(self):
        try:
            await self._execute(quit=sc_pb.RequestQuit())
        except ConnectionAlreadyClosed:
            pass
