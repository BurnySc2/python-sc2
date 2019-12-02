import logging

from s2clientprotocol import sc2api_pb2 as sc_pb

from .player import Computer
from .protocol import Protocol

logger = logging.getLogger(__name__)

class Controller(Protocol):
    def __init__(self, ws, process):
        super().__init__(ws)
        self.__process = process

    @property
    def running(self):
        return self.__process._process is not None

    async def create_game(self, game_map, players, realtime, random_seed=None):
        assert isinstance(realtime, bool)
        req = sc_pb.RequestCreateGame(local_map=sc_pb.LocalMap(map_path=str(game_map.relative_path)), realtime=realtime)
        if random_seed is not None:
            req.random_seed = random_seed

        for player in players:
            p = req.player_setup.add()
            p.type = player.type.value
            if isinstance(player, Computer):
                p.race = player.race.value
                p.difficulty = player.difficulty.value
                p.ai_build = player.ai_build.value

        logger.info("Creating new game")
        logger.info(f"Map:     {game_map.name}")
        logger.info(f"Players: {', '.join(str(p) for p in players)}")
        result = await self._execute(create_game=req)
        return result
