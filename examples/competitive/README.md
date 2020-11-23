# Example competitive bot

This is a small example bot that should work with [AI-Arena](https://aiarena.net/), [Sc2AI](https://sc2ai.net/) and [Probots](https://eschamp.com/shows/probots/).

Copy the "python-sc2/sc2" folder inside this folder before distributing your bot for competition. This prevents the default python-sc2 installation to be loaded/imported, which could be vastly outdated.

Change the bot race in the [run.py](run.py) (line 8) and in the [ladderbots.json](ladderbots.json) file (line 4).

Zip the entire folder to a <YOUR_BOTS_NAME_HERE>.zip file. Make sure that the files are in the root folder of the zip.
https://aiarena.net/wiki/getting-started/#wiki-toc-bot-zip

## AI Arena

To compete on AI Arena...

Make sure to notify AI-Arena if you need additional requirements (python packages) for your bot to run. A "requirements.txt" is not going to be read.

Make an account on https://aiarena.net/ and upload the zip file as a new bot. Make sure to select the right race and bot type (python).

## Sc2AI & Probots

The [ladderbots.json](ladderbots.json) file contains parameters to support play for Sc2AI and Probots. Don't forget to update them!

Both Sc2AI and Probots will pip install your "requirements.txt" file for you.
