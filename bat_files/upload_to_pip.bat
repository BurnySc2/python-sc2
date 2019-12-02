:: A small script to publish a new version of burnysc2 to pypi

cd ..

pip install --upgrade pipenv
pip install --upgrade setuptools wheel
pip install --upgrade twine

:: Remove /dist and /build folder recursively so that there are no errors when uploading to pypi: error 400 package already exists
RD /Q /S dist
RD /Q /S build
RD /Q /S burnysc2.egg-info

TIMEOUT 1

:: Create data in /dist folder
python setup.py sdist bdist_wheel

:: Upload /dist folder to pip, pypi login required
twine upload dist/* --verbose

TIMEOUT 1

:: Cleanup: remove folder dist and build
RD /Q /S dist
RD /Q /S build
RD /Q /S burnysc2.egg-info

