:: pip install sphinx
:: pip install sphinx-autodoc-typehints

:: Run this script to generate the documentation html files from scratch
:: Use this before merging from dev branch to master branch

sphinx-build -a -E -b html . ../docs