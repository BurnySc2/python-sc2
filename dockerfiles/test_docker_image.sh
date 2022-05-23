# This script is meant for development, which produces fresh images and then runs tests

# Set which versions to use
export VERSION_NUMBER=${VERSION_NUMBER:-1.0.0}
export PYTHON_VERSION=${PYTHON_VERSION:-3.10}
export SC2_VERSION=${SC2_VERSION:-4.10}

# Build images
docker build -f dockerfiles/Dockerfile -t burnysc2/python-sc2-docker:latest --build-arg PYTHON_VERSION=$PYTHON_VERSION --build-arg SC2_VERSION=$SC2_VERSION .

# Delete previous container if it exists
docker rm -f test_container

# Start container, override the default entrypoint
# https://docs.docker.com/storage/bind-mounts/#use-a-read-only-bind-mount
docker run -it -d \
  --name test_container \
  --mount type=bind,source="$(pwd)",destination=/root/python-sc2,readonly \
  --entrypoint /bin/bash \
  burnysc2/python-sc2-docker:latest

# Install python-sc2, via mount the python-sc2 folder will be available
docker exec -it test_container bash -c "pip install poetry \
    && cd python-sc2 && poetry install --no-dev"

# Run various test bots
docker exec -it test_container bash -c "cd python-sc2 && poetry run python test/travis_test_script.py test/autotest_bot.py"
docker exec -it test_container bash -c "cd python-sc2 && poetry run python test/run_example_bots_vs_computer.py"

# Command for entering the container to debug if something went wrong:
# docker exec -it test_container bash
