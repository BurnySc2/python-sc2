[![Actions Status](https://github.com/BurnySc2/python-sc2/workflows/Tests/badge.svg)](https://github.com/BurnySc2/python-sc2/actions)

# A StarCraft II API Client for Python 3

An easy-to-use library for writing AI Bots for StarCraft II in Python 3. The ultimate goal is simplicity and ease of use, while still preserving all functionality. A really simple worker rush bot should be no more than twenty lines of code, not two hundred. However, this library intends to provide both high and low level abstractions.

**This library (currently) covers only the raw scripted interface.** At this time I don't intend to add support for graphics-based interfaces.

The [documentation can be found here](https://burnysc2.github.io/python-sc2/docs/index.html).
For bot authors, looking directly at the files in the [sc2 folder](/sc2) can also be of benefit: bot_ai.py, unit.py, units.py, client.py, game_info.py and game_state.py. Most functions in those files have docstrings, example usages and type hinting.

I am planning to change this fork more radically than the main repository, for bot performance benefits and to add functions to help new bot authors. This may break older bots in the future, however I try to add deprecationwarnings to give a heads up notification. This means that the [video tutorial made by sentdex](https://pythonprogramming.net/starcraft-ii-ai-python-sc2-tutorial/) is outdated and does no longer directly work with this fork.

For a list of ongoing changes and differences to the main repository of Dentosal, [check here](https://github.com/BurnySc2/python-sc2/issues/4).

## Installation

By installing this library you agree to be bound by the terms of the [AI and Machine Learning License](http://blzdistsc2-a.akamaihd.net/AI_AND_MACHINE_LEARNING_LICENSE.html).

For this fork, you'll need Python 3.7 or newer.

Install the pypi package:
```
pip install --upgrade pipenv burnysc2
```
or directly from develop branch:
```
pip install pipenv
pip install --upgrade --force-reinstall https://github.com/BurnySc2/python-sc2/archive/develop.zip
```
Both commands will use the `sc2` library folder, so you will not be able to have Dentosal's and this fork installed at the same time, unless you use virtual environments or pipenv.

You'll need an StarCraft II executable. If you are running Windows or macOS, just install the normal SC2 from blizzard app. [The free starter edition works too](https://us.battle.net/account/sc2/starter-edition/). Linux users get the best experience by installing the Windows version of StarCraft II with [Wine](https://www.winehq.org). Linux user can also use the [Linux binary](https://github.com/Blizzard/s2client-proto#downloads), but it's headless so you cannot actually see the game.

You probably want some maps too. Official map downloads are available from [Blizzard/s2client-proto](https://github.com/Blizzard/s2client-proto#downloads). Notice: the map files are to be extracted into *subdirectories* of the `install-dir/Maps` directory.
Maps that are run on the [SC2 AI Ladder](http://sc2ai.net/) and [SC2 AI Arena](https://ai-arena.net/) can be downloaded [from the sc2ai wiki](http://wiki.sc2ai.net/Ladder_Maps) and [the ai-arena wiki](https://ai-arena.net/wiki/getting-started/#wiki-toc-maps).

### Running

After installing the library, a StarCraft II executable, and some maps, you're ready to get started. Simply run a bot file to fire up an instance of StarCraft II with the bot running. For example:

```python
python3 examples/protoss/cannon_rush.py
```

If you installed StarCraft II on Linux with Wine or Lutris, set the following environment variables (either globally or within your development environment, e.g. Pycharm: `Run -> Edit Configurations -> Environment Variables`):

```sh
SC2PF=WineLinux
WINE=usr/bin/wine
# Or a wine binary from lutris:
# WINE=/home/burny/.local/share/lutris/runners/wine/lutris-4.20-x86_64/bin/wine64
# Default Lutris StarCraftII Installation path:
SC2PATH=/home/burny/Games/battlenet/drive_c/Program Files (x86)/StarCraft II/
```

## Example

As promised, worker rush in less than twenty lines:

```python
import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer

class WorkerRushBot(sc2.BotAI):
    async def on_step(self, iteration: int):
        if iteration == 0:
            for worker in self.workers:
                self.do(worker.attack(self.enemy_start_locations[0]))

run_game(maps.get("Abyssal Reef LE"), [
    Bot(Race.Zerg, WorkerRushBot()),
    Computer(Race.Protoss, Difficulty.Medium)
], realtime=True)
```

This is probably the simplest bot that has any realistic chances of winning the game. I have ran it against the medium AI a few times, and once in a while, it wins.

You can find more examples in the [`examples/`](/examples) folder.

## API Configuration Options

The API supports a number of options for configuring how it operates.

### `raw_affects_selection`
Setting this to true improves bot performance by a little bit.
```python
class MyBot(sc2.BotAI):
    def __init__(self):
        self.raw_affects_selection = True
```

### `distance_calculation_method`
The distance calculation method:
- 0 for raw python
- 1 for scipy pdist
- 2 for scipy cdist
```python
class MyBot(sc2.BotAI):
    def __init__(self):
        self.distance_calculation_method = 2
```

### `game_step`
On game start or in any frame actually, you can set the game step. This controls how often your bot's `step` method is called.  
__Do not set this in the \_\_init\_\_ function as the client will not have been initialized yet!__
```python
class MyBot(sc2.BotAI):
    def __init__(self):
        pass  # don't set it here!

    async def on_start(self):
        self.client.game_step = 2
```

## Community - Help and support

You have questions but don't want to create an issue? Join the [Starcraft 2 AI Discord server](https://discordapp.com/invite/zXHU4wM) or [ai-arena.net Discord server](https://discord.gg/yDBzbtC). Questions about this repository can be asked in text channel #python. There are discussions and questions about SC2 bot programming and this repository every day.

## Bug reports, feature requests and ideas

If you have any issues, ideas or feedback, please create [a new issue](https://github.com/BurnySc2/python-sc2/issues/new). Pull requests are also welcome!


## Contributing & style guidelines

Git commit messages use [imperative-style messages](https://stackoverflow.com/a/3580764/2867076), start with capital letter and do not have trailing commas.
