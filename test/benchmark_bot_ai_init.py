from test.test_pickled_data import MAPS, build_bot_object_from_pickle_data, load_map_pickle_data
from typing import Any, List, Tuple

# Load pickle files outside of benchmark
MAP_PICKLE_DATA: List[Tuple[Any, Any, Any]] = [load_map_pickle_data(path) for path in MAPS]


def _test_run_bot_ai_init_on_all_maps():
    for data in MAP_PICKLE_DATA:
        build_bot_object_from_pickle_data(*data)


def test_bench_bot_ai_init(benchmark):
    _result = benchmark(_test_run_bot_ai_init_on_all_maps)


# Run this file using
# poetry run pytest test/benchmark_bot_ai_init.py --benchmark-compare --benchmark-min-rounds=5
