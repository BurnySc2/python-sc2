from test.test_pickled_data import MAPS, get_map_specific_bot


def _test_run_bot_ai_init_on_all_maps():
    # BENCHMARK OLD: 4.4036 mean

    # BENCHMARK DATACLASS with converting observation: 1.7375 - 1.7614 mean
    # BENCHMARK DATACLASS with converting each unit from protobuf: 1.7656 - 1.8001 mean

    # BENCHMARK PYDANTIC: 2.0253 mean

    for map_ in MAPS:
        _result = get_map_specific_bot(map_)


def test_bench_bot_ai_init(benchmark):
    _result = benchmark(_test_run_bot_ai_init_on_all_maps)
    # assert check_result(result, correct_result)


# Run this file using
# poetry run pytest test/benchmark_bot_ai_init.py --benchmark-compare
