# Buildable via command from root folder
# docker build -t test_image -f test/Dockerfile --build-arg PYTHON_VERSION=3.8 --build-arg SC2_VERSION=4.10 .

# For more info see https://github.com/BurnySc2/python-sc2-docker
ARG PYTHON_VERSION=3.8
ARG SC2_VERSION=4.10

FROM burnysc2/python-sc2-docker:py_${PYTHON_VERSION}-sc2_${SC2_VERSION}-v1.0.0

# Copy files from the current commit (the python-sc2 folder) to root
ADD . /root/python-sc2

# Install the python-sc2 library and its requirements (s2clientprotocol etc.) to python
WORKDIR /root/python-sc2
RUN pip install poetry
# This will not include dev dependencies
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes
RUN pip install -r requirements.txt

# This will be executed during the container run instead:
# docker run test_image -c "poetry run python examples/protoss/cannon_rush.py"

ENTRYPOINT [ "/bin/bash" ]
