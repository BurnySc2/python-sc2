:: A small script to

:: Generate ids from stable id
:: Generate all pickle files again
:: Generate dicts from data.json
:: Generate the documentation


:: No requirements
cd ..
python generate_id_constants_from_stableid.py

TIMEOUT 1

:: Next commands require pipenv, set up dev and update Pipfile.lock
pip install --upgrade pipenv
pipenv install --dev
pipenv update

TIMEOUT 1

:: Remove previous pickle data
:: RD /Q /S .\test\pickle_data
:: Re-generate them
pipenv run ".\test\generate_pickle_files_bot.py"

TIMEOUT 1

:: Requires at least one pickle file
python generate_dicts_from_data_json.py

TIMEOUT 1

:: Remove previous documentation
RD /Q /S docs
:: Generate documentation
:: Use this before merging from dev branch to gh-pages branch
cd docs_generate
pipenv run sphinx-build -a -E -b html . ../docs
