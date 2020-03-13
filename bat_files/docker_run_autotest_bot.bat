:: Requirements: Docker installed and running

:: This script runs the test bot on a docker client

cd ..

docker rm -f app1
docker build -t test_image -f test/Dockerfile_3.7 .
docker run -it -d --name app1 test_image
docker exec -i app1 bash -c "python test/travis_test_script.py test/autotest_bot.py"
::docker exec -i app1 bash -c "python test/autotest_bot.py"
docker rm -f app1
