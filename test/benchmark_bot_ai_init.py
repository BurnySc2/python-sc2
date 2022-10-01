from test.test_pickled_data import MAPS, get_map_specific_bot


def _test_run_bot_ai_init_on_all_maps():
    # Run bot initialization from pickled files via get_map_specific_bot()
    for map_ in MAPS:
        _result = get_map_specific_bot(map_)


def test_bench_bot_ai_init(benchmark):
    _result = benchmark(_test_run_bot_ai_init_on_all_maps)


# Run this file using
# poetry run pytest test/benchmark_bot_ai_init.py --benchmark-compare
