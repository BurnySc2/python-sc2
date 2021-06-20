*****************************
Using docker to run SC2 bots
*****************************
This is a small overview on how to use docker to run 2 bots (here: python-sc2 bots) against each other using the linux binary SC2 client.
For a quick summary of commands, scroll to the bottom.

Requirements
------------
- Docker installed and running
- Internet
- Doesn't require a GPU

Pulling the Docker image
------------------------
The SC2 AI community has decided to stay on Python3.7 for a while. I'll try to update the docker image as soon as a new linux binary is released, or create a pull request at https://github.com/BurnySc2/python-sc2-docker ::

    docker pull burnysc2/python-sc2-docker:release-python_3.7-sc2_4.10_arenaclient_burny

Deleting previous containers
-----------------------------
To remove the previously used ``app`` container::

    docker run -it -d --name app test_image

Launching a new container
--------------------------
The following command launches a new container in interactive mode, which means it will not shut down once it is done running::

    docker run -it -d --name app burnysc2/python-sc2-docker:release-python_3.7-sc2_4.10_arenaclient_burny

Install bot requirements
-------------------------
The command ``docker exec -i app poetry add "burnysc2>=0.12.12"`` installs the ``burnysc2`` dependencies in the docker container. Add more libraries as needed. You can also create your custom docker image so you do not have to re-install the dependencies every time you create a new container.

Since the linux SC2 binary is usually outdated (last update as of this writing was summer of 2019), you will likely have to replace your IDs with older IDs, which can be found here: https://github.com/BurnySc2/python-sc2/tree/linux-4.10/sc2/ids

If you want your bots to play against a compiled bot (``.exe``), you will have to install ``wine``. I have not included wine in the docker image to keep the image as small as possible.

Copying Bots to the container
------------------------------
The bots in the container need to be located under ``app:/root/StarCraftII/Bots/<bot_name>``
A copy command could be ``docker cp examples/competetive/. app:/root/StarCraftII/Bots/my_bot`` if you are in the main ``python-sc2` directory, which copies the competetive example bot to the container. The bots will be launched via ``run.py``. The ``ladderbots.json`` might not be needed.
Don't forget to copy the python-sc2/sc2 folder, or else an older version might be used (on import) and your bot might not work correctly.

For more info about competitive bots setup, see:

https://github.com/BurnySc2/python-sc2/tree/develop/examples/competitive or https://eschamp.discourse.group/t/simple-starcraft-2-bot-template-to-get-started/155

Copying the runner to the container
------------------------------------
You will have to configure the ``custom_run_local.py`` file (ctrl+f for ``def main()``).
It can be found here: https://github.com/BurnySc2/python-sc2/tree/develop/bat_files/docker/custom_run_local.py

You may also customize the arenaclient ``settings.json`` (e.g. max game time) which is located under ``/root/aiarena-client/arenaclient/proxy/settings.json``
Click here to check which settings are available: https://github.com/BurnySc2/aiarena-client/blob/a1cd2e9314e7fd2accd0e69aa77d89a9978e619c/arenaclient/proxy/server.py#L164-L170

After you are done customizing which matches should be played, run the following to finalize your setup::

    docker cp bat_files/docker/custom_run_local.py app:/root/aiarena-client/arenaclient/run_local.py

Running the match(es)
---------------------
Now you are ready to let docker run your matches (headless)::

    docker exec -i app poetry run python /root/aiarena-client/arenaclient/run_local.py

Copying the replay from container to host machine
--------------------------------------------------------------
To copy the ``results.json`` to the host machine to analyse the results, use::

    mkdir -p bat_files/temp
    docker cp app:/root/aiarena-client/arenaclient/proxy/results.json bat_files/temp/results.json

To copy all newly generated replays from the container, use::

    mkdir -p bat_files/temp/replays
    docker cp app:/root/StarCraftII/Replays/. bat_files/temp/replays

Summary using a shell script
-----------------------------
For a full runner script, see:

https://github.com/BurnySc2/python-sc2/tree/develop/bat_files/docker/docker_run_bots.sh

Docker cleanup
---------------
See also: https://docs.docker.com/config/pruning/
Force removing all containers (including running)::

    docker rm -f $(docker ps -aq)

Removing all images::

    docker rmi $(docker images -q)

Prune everything docker related::

    docker system prune --volumes