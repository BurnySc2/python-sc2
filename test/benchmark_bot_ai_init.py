from test.test_pickled_data import MAPS, build_bot_object_from_pickle_data, load_map_pickle_data
from typing import Any, List, Tuple


def _test_run_bot_ai_init_on_all_maps(pickle_data: List[Tuple[Any, Any, Any]]):
    for data in pickle_data:
        build_bot_object_from_pickle_data(*data)


def test_bench_bot_ai_init(benchmark):
    # Load pickle files outside of benchmark
    map_pickle_data: List[Tuple[Any, Any, Any]] = [load_map_pickle_data(path) for path in MAPS]
    _result = benchmark(_test_run_bot_ai_init_on_all_maps, map_pickle_data)


# Run this file using
# poetry run pytest test/benchmark_bot_ai_init.py --benchmark-compare --benchmark-min-rounds=5
