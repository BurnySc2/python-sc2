"""
This script is made as a wrapper for sc2 bots to set a timeout to the bots (in case they can't find the last enemy structure or the game is ending in a draw)
Ideally this script should be done with a bot that terminates on its own after certain things have been achieved, e.g. testing if the bot can expand at all, and then terminates after it has successfully expanded.

Usage: see .bat files in /bat_files/ folder
cd into python-sc2/ directory
docker build -t test_image -f test/Dockerfile .
docker run test_image -c "python test/travis_test_script.py test/autotest_bot.py"

Or if you want to run from windows:
poetry run python test/travis_test_script.py test/autotest_bot.py
"""
import subprocess
import sys
import time

from loguru import logger

retries = 3
# My maxout bot (reaching 200 supply in sc2) took 110 - 140 real seconds for 7 minutes in game time
# How long the script should run before it will be killed:
timeout_time = 8 * 60  # 8 minutes real time

if len(sys.argv) > 1:
    # Attempt to run process with retries and timeouts
    t0 = time.time()
    process, result = None, None
    output_as_list = []
    i = 0
    for i in range(retries):
        t0 = time.time()

        process = subprocess.Popen(["python", sys.argv[1]], stdout=subprocess.PIPE)
        try:
            # Stop the current bot if the timeout was reached - the bot needs to finish a game within 3 minutes real time
            result = process.communicate(timeout=timeout_time)
        except subprocess.TimeoutExpired:
            continue
        out, err = result
        result = out.decode("utf-8")
        if process.returncode is not None and process.returncode != 0:
            # Bot has thrown an error, try again
            logger.info(
                f"Bot has thrown an error with error code {process.returncode}. This was try {i+1} out of {retries}."
            )
            continue

        # Break as the bot run was successful
        break

    if process.returncode is not None:
        # Reformat the output into a list
        logger.info_output: str = result
        linebreaks = [
            ["\r\n", logger.info_output.count("\r\n")],
            ["\r", logger.info_output.count("\r")],
            ["\n", logger.info_output.count("\n")],
        ]
        most_linebreaks_type = max(linebreaks, key=lambda x: x[1])
        linebreak_type, linebreak_count = most_linebreaks_type
        output_as_list = logger.info_output.split(linebreak_type)
        logger.info("Travis test script, bot output:\r\n{}\r\nEnd of bot output".format("\r\n".join(output_as_list)))

    time_taken = time.time() - t0

    # Bot was not successfully run in time, returncode will be None
    if process.returncode is None or process.returncode != 0:
        logger.info(
            f"Exiting with exit code 5, error: Attempted to launch script {sys.argv[1]} timed out after {time_taken} seconds. Retries completed: {i}"
        )
        sys.exit(5)

    # process.returncode will always return 0 if the game was run successfully or if there was a python error (in this case it returns as defeat)
    logger.info("Returncode: {}".format(process.returncode))
    logger.info("Game took {} real time seconds".format(round(time.time() - t0, 1)))
    if process is not None and process.returncode == 0:
        for line in output_as_list:
            # This will throw an error even if a bot is called Traceback
            if "Traceback " in line:
                logger.info("Exiting with exit code 3")
                sys.exit(3)
        logger.info("Exiting with exit code 0")
        sys.exit(0)

    # Exit code 1: game crashed I think
    logger.info("Exiting with exit code 1")
    sys.exit(1)

# Exit code 2: bot was not launched
logger.info("Exiting with exit code 2")
sys.exit(2)
