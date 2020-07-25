cd ..
pipenv run python -m cProfile -o zerg_rush.prof examples/zerg/zerg_rush.py
pipenv run snakeviz zerg_rush.prof
