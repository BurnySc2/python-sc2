# A StarCraft II API Client for Python 3

An easy-to-use library for writing AI Bots for StarCraft II in Python 3. The ultimate goal is simplicity and ease of use, while still preserving all functionality. A really simple worker rush bot should be no more than twenty lines of code, not two hundred. However, this library intends to provide both high and low level abstractions.

**This library (currently) covers only the raw scripted interface.** At this time I don't intend to add support for graphics-based interfaces.

Documentation is in [the Wiki](https://github.com/Dentosal/python-sc2/wiki).

For automatically running multiple matches, check out [Dentosal/sc2-bot-match-runner](https://github.com/Dentosal/sc2-bot-match-runner).

## Installation

By installing this library you agree to be bound by the terms of the [AI and Machine Learning License](http://blzdistsc2-a.akamaihd.net/AI_AND_MACHINE_LEARNING_LICENSE.html).

You'll need Python 3.6 or newer.

```
pip3 install --user --upgrade sc2
```

Please note that not all commits are released to PyPI. Releases are tagged with version number. You can see latest released versions from [tags page](https://github.com/Dentosal/python-sc2/tags).

You'll also need an StarCraft II executable. If you are running Windows or macOS, just install the normal SC2 from blizzard app. [The free starter edition works too.](https://us.battle.net/account/sc2/starter-edition/). Linux users get the best experience by installing the Windows version of StarCraft II with [Wine](https://www.winehq.org). Linux user can also use the [Linux binary](https://github.com/Blizzard/s2client-proto#downloads), but it's headless so you cannot actually see the game.

You probably want some maps too. Official map downloads are available from [Blizzard/s2client-proto](https://github.com/Blizzard/s2client-proto#downloads). Notice: the map files are to be extracted into *subdirectories* of the `install-dir/Maps` directory.

### Running

After installing the library, a StarCraft II executable, and some maps, you're ready to get started. Simply run a bot file to fire up an instance of StarCraft II with the bot running. For example:

```
python3 examples/protoss/cannon_rush.py
```

If you installed StarCraft II on Linux with Wine, set the `SC2PF` environment variable to `WineLinux`:

```
SC2PF=WineLinux python3 examples/protoss/cannon_rush.py
```

## Example

As promised, worker rush in less than twenty lines:

```python
import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer

class WorkerRushBot(sc2.BotAI):
    async def on_step(self, iteration):
        if iteration == 0:
            for worker in self.workers:
                self.do(worker.attack(self.enemy_start_locations[0]))

run_game(maps.get("Abyssal Reef LE"), [
    Bot(Race.Zerg, WorkerRushBot()),
    Computer(Race.Protoss, Difficulty.Medium)
], realtime=True)
```

This is probably the simplest bot that has any realistic chances of winning the game. I have ran it against the medium AI a few times, and once in a while it wins.

You can find more examples in the [`examples/`](/examples) folder.

## Help and support

You have questions but don't want to create an issue? Join the [Starcraft 2 AI Discord](https://discordapp.com/invite/zXHU4wM). Questions about this repository can be asked in channel #python-sc2.

## Bug reports, feature requests and ideas

If you have any issues, ideas or feedback, please create [a new issue](https://github.com/Dentosal/python-sc2/issues/new). Pull requests are also welcome!


## Contributing & style guidelines

Git commit messages use [imperative-style messages](https://stackoverflow.com/a/3580764/2867076), start with capital letter and do not have trailing commas.
