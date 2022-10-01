from test.test_pickled_data import MAPS, get_map_specific_bot
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from sc2.bot_ai import BotAI


def _run_prepare_units(bot_objects: List["BotAI"]):
    for bot_object in bot_objects:
        bot_object._prepare_units()


def test_bench_prepare_units(benchmark):
    bot_objects = [get_map_specific_bot(map_) for map_ in MAPS]
    _result = benchmark(_run_prepare_units, bot_objects)


# Run this file using
# poetry run pytest test/benchmark_prepare_units.py --benchmark-compare
