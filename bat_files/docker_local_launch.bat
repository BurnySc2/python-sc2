:: Requirements: Docker installed and running

:: This script runs the test bot on a docker client

cd ..

docker rm -f app
docker build -t test_image -f test/Dockerfile .
docker run -it -d --name app test_image
docker exec -i app bash -c "python test/travis_test_script.py test/autotest_bot.py"
docker rm -f app
