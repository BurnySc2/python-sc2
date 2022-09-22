import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


from test.test_pickled_data import get_map_specific_bot, MAPS


def _test_run_bot_ai_init_on_all_maps():
    # BENCHMARK OLD: 4.4036 mean

    # BENCHMARK DATACLASS: 1.6229 mean

    # BENCHMARK PYDANTIC: 2.0253 mean

    for map_ in MAPS:
        _result = get_map_specific_bot(map_)



def test_bench_bot_ai_init(benchmark):
    _result = benchmark(_test_run_bot_ai_init_on_all_maps)
    # assert check_result(result, correct_result)


# Run this file using
# poetry run pytest test/benchmark_bot_ai_init.py --benchmark-compare
