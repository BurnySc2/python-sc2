# Set up StarCraft II Test Environment for python-sc2 bots (not pysc2 bots!)
ARG PYTHON_VERSION=3.10

# Use an official debian stretch slim release as a base image
FROM python:$PYTHON_VERSION-slim
MAINTAINER Burny <gamingburny@gmail.com>

ARG SC2_VERSION=4.10

# Debugging purposes
RUN echo $PYTHON_VERSION
RUN echo $SC2_VERSION

USER root

# Update system
RUN apt-get update \
    && apt-get upgrade --assume-yes --quiet=2

# Update and install packages for SC2 development environment
# gcc to compile packages
# libc6-dev required by gcc: /usr/local/include/python3.12/Python.h:23:12: fatal error: stdlib.h: No such file or directory
# git, unzip and wget for download and extraction
# rename to rename maps
# tree for debugging
RUN apt-get install --assume-yes --no-install-recommends --no-show-upgraded \
    gcc \
    libc6-dev \
    git  \
    unzip \
    curl \
    rename \
    tree

# Set working directory to root, this uncompresses StarCraftII below to folder /root/StarCraftII
WORKDIR /root/

# Download and uncompress StarCraftII from https://github.com/Blizzard/s2client-proto#linux-packages and remove zip file
# If file is locally available, use this instead:
#COPY SC2.4.10.zip /root/
RUN curl http://blzdistsc2-a.akamaihd.net/Linux/SC2.$SC2_VERSION.zip -o "SC2.$SC2_VERSION.zip" \
    && unzip -q -P iagreetotheeula SC2.$SC2_VERSION.zip \
    && rm SC2.$SC2_VERSION.zip

# Remove Battle.net folder
RUN rm -rf /root/StarCraftII/Battle.net/* \
    # Remove Shaders folder
    && rm -rf /root/StarCraftII/Versions/Shaders*

# Create a symlink for the maps directory
RUN ln -s /root/StarCraftII/Maps /root/StarCraftII/maps \
    # Remove the Maps that come with the SC2 client
    && rm -rf /root/StarCraftII/maps/*

# Change to maps folder
WORKDIR /root/StarCraftII/maps/

# Maps are available here https://github.com/Blizzard/s2client-proto#map-packs and here https://sc2ai.net/wiki/maps/
# Download and uncompress StarCraftII Maps, remove zip file - using "maps" instead of "Maps" as target folder

# Get sc2ai.net ladder maps
# -L param follows links https://stackoverflow.com/a/2663023/10882657
RUN curl -L https://sc2ai.net/wiki/184/plugin/attachments/download/9/ -o 1.zip \
    && curl -L https://sc2ai.net/wiki/184/plugin/attachments/download/14/ -o 2.zip \
    && curl -L https://sc2ai.net/wiki/184/plugin/attachments/download/21/ -o 3.zip \
    && curl -L https://sc2ai.net/wiki/184/plugin/attachments/download/35/ -o 4.zip \
    && curl -L https://sc2ai.net/wiki/184/plugin/attachments/download/36/ -o 5.zip \
    && curl -L https://sc2ai.net/wiki/184/plugin/attachments/download/38/ -o 6.zip \
    && curl -L https://sc2ai.net/wiki/184/plugin/attachments/download/39/ -o 7.zip \
    && unzip -q -o '*.zip' \
    && rm *.zip

# Get official blizzard maps
RUN curl http://blzdistsc2-a.akamaihd.net/MapPacks/Ladder2019Season3.zip -o Ladder2019Season3.zip \
    && unzip -q -P iagreetotheeula -o 'Ladder2019Season3.zip' \
    && mv Ladder2019Season3/* . \
    && rm Ladder2019Season3.zip \
    && rm -r Ladder2019Season3

# Get v5.0.6 maps
RUN curl -L https://github.com/shostyn/sc2patch/raw/4987d4915b47c801adbc05e297abaa9ca2988838/Maps/506.zip -o 506.zip \
    && unzip -q -o '506.zip' \
    && rm 506.zip

# Get flat and empty maps
RUN curl http://blzdistsc2-a.akamaihd.net/MapPacks/Melee.zip -o Melee.zip \
    && unzip -q -P iagreetotheeula -o 'Melee.zip' \
    && mv Melee/* . \
    && rm Melee.zip \
    && rm -r Melee

# Remove LE suffix from file names
RUN rename -v 's/LE.SC2Map/.SC2Map/' *.SC2Map

# List all map files
RUN tree

WORKDIR /root/

ENTRYPOINT [ "/bin/bash" ]

# To run a python-sc2 bot:
# Install python-sc2 and requirements via pip:
# pip install --upgrade https://github.com/BurnySc2/python-sc2/archive/develop.zip

# To run an example bot, copy one to your container and then run it with python:
# python /your-bot.py