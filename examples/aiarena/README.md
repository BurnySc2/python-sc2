This is a small example bot and upload instruction on how to upload a bot to [AI-Arena](https://ai-arena.net/).

Copy the "python-sc2/sc2" folder inside this folder before uploading your bot to AI-Arena. This prevents the default python-sc2 installation to be loaded/imported, which could be vastly outdated.

Change the bot race in the run.py (line 8).

Zip the entire folder to a ExampleBot.zip file. Make sure that the files are in the root folder of the zip.
https://ai-arena.net/wiki/getting-started/#wiki-toc-bot-zip

Make sure to notify AI-Arena if you need additional requirements (python packages) for your bot to run. A "requirements.txt" is not going to be read.

Make an account on https://ai-arena.net/ and upload the zip file as a new bot. Make sure to select the right race and bot type (python).
