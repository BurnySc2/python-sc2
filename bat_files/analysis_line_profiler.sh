# Add a '@profile' as decorator in front of a function to tell line_profiler which function to analyse
cd ..
pipenv run kernprof -l examples/zerg/zerg_rush.py
pipenv run python -m line_profiler zerg_rush.py.lprof > line_profiler_result.txt
rm zerg_rush.py.lprof
