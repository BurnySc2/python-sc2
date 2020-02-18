import argparse

import sys
import asyncio

import sc2
from sc2 import Race
from sc2.player import Bot

from zerg.zerg_rush import ZergRushBot


def main(is_host, pc):
    if args.portconfig:
        portconfig = sc2.portconfig.Portconfig.from_json(pc)
    else:
        assert args.host, "Must be host if portconfig is not given"
        portconfig = sc2.portconfig.Portconfig()
        print(portconfig.as_json)

    player_config = [Bot(Race.Zerg, None), Bot(Race.Zerg, None)]

    player_config[0 if is_host else 1].ai = ZergRushBot()

    if is_host:
        g = sc2.main._host_game(sc2.maps.get("Abyssal Reef LE"), player_config, realtime=False, portconfig=portconfig)
    else:
        g = sc2.main._join_game(player_config, realtime=False, portconfig=portconfig)

    result = asyncio.get_event_loop().run_until_complete(g)
    print(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run an external game")
    parser.add_argument("--host", action="store_true", help="host a game")
    parser.add_argument("portconfig", type=str, nargs="?", help="port configuration as json")
    args = parser.parse_args()

    main(args.host, args.portconfig)
