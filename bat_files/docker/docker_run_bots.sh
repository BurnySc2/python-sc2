# Run this file from main folder 'python-sc2'
# sh bat_file/docker/docker_run_bots.sh

docker pull burnysc2/python-sc2-docker:release-python_3.7-sc2_4.10_arenaclient_burny

# Force-remove previous container called 'app'
docker rm -f app

# Create container
docker run -it -d --name app burnysc2/python-sc2-docker:release-python_3.7-sc2_4.10_arenaclient_burny

# List available maps
docker exec -i app bash -c "ls -l /root/StarCraftII/maps"

# Install bot requirements
docker exec -i app poetry add "burnysc2>=0.12.12"

# Copy bots from bat_files/docker/
docker cp bat_files/docker/basic_bot/. app:/root/StarCraftII/Bots/basic_bot
docker cp bat_files/docker/loser_bot/. app:/root/StarCraftII/Bots/loser_bot

# Copy python-sc2/sc2 folder to bots
docker cp sc2/. app:/root/StarCraftII/Bots/basic_bot/sc2
docker cp sc2/. app:/root/StarCraftII/Bots/loser_bot/sc2

# Copy over custom run_local.py
# See https://github.com/BurnySc2/aiarena-client for original source, or https://github.com/aiarena/aiarena-client (older commits)
docker cp bat_files/docker/custom_run_local.py app:/root/aiarena-client/arenaclient/run_local.py

# Start arenaclient server
# docker exec -i app python /root/aiarena-client/arenaclient/proxy/server.py -f &
# Alternatively set in Dockerfile as last line:
# ENTRYPOINT [ "python", "proxy/server.py", "-f" ]

# Run the match(es)
docker exec -i app poetry run python /root/aiarena-client/arenaclient/run_local.py

# Display error logs
docker exec -i app bash -c "tree /root/aiarena-client/arenaclient/logs"
docker exec -i app bash -c "echo Basic bot error log:"
docker exec -i app bash -c "cat /root/aiarena-client/arenaclient/logs/1/basic_bot/stderr.log"
docker exec -i app bash -c "echo Loser bot error log:"
docker exec -i app bash -c "cat /root/aiarena-client/arenaclient/logs/1/loser_bot/stderr.log"
docker exec -i app bash -c "echo Proxy results.json:"
docker exec -i app bash -c "cat /root/aiarena-client/arenaclient/proxy/results.json"

# Display result.json
docker exec -i app bash -c "cat /root/aiarena-client/arenaclient/proxy/results.json"

# Copy results.json to host machine
mkdir -p bat_files/temp
docker cp app:/root/aiarena-client/arenaclient/proxy/results.json bat_files/temp/results.json

# Copy replay to host machine
docker exec -i app bash -c "tree /root/StarCraftII/Replays"
mkdir -p bat_files/temp/replays
docker cp app:/root/StarCraftII/Replays/. bat_files/temp/replays


