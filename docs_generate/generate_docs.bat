:: pip install sphinx
:: pip install sphinx-autodoc-typehints

:: Run this script to generate the documentation html files from scratch
:: Use this before merging from dev branch to gh-pages branch

:: Remove docs folder and generate fresh from start
rm -r ../docs

:: Generate documentation
sphinx-build -a -E -b html . ../docs
