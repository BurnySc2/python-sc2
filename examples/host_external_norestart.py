import sc2
from examples.zerg.zerg_rush import ZergRushBot
from sc2.data import Race
from sc2.file_maps import get as get_maps
from sc2.main import _host_game_iter
from sc2.player import Bot


def main():
    portconfig = sc2.portconfig.Portconfig()
    print(portconfig.as_json)

    player_config = [Bot(Race.Zerg, ZergRushBot()), Bot(Race.Zerg, None)]

    for g in _host_game_iter(
        get_maps("AbyssalReefLE"),
        player_config,
        realtime=False,
        portconfig=portconfig,
    ):
        print(g)


if __name__ == "__main__":
    main()
