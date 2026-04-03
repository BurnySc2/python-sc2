# AI Generated Changelog  (burnysc2 + original sc2 — merged)

All notable changes to this project will be documented in this file.

This is a **merged changelog** covering two related projects:
- **burnysc2** — the active fork maintained by BurnySc2 (PyPI: `burnysc2`)
- **original sc2** — the deprecated upstream by Dentosal (PyPI: `sc2`, archived)

The fork point is **version 0.11.2** (2019-12-01), after which the two projects diverged.
The burnysc2 releases are listed first (newest → oldest),
followed by the original sc2 releases.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [7.2.0] - 2026-03-30

### Added
- Add pyrefly ignores and update pyrefly version
- Bump to support Python 3.9

### Fixed
- Fixes protobuf test
- Fix mass_reaper type hints
- Fix mass_reaper bot for python3.9
- Fix already_pending check order
- Fix ramp finding
- Fix types for test folder
- Fix types for example folder
- Fix types for bot_ai.py
- Fix types for bot_ai_internal.py
- Fix type hints for client.py
- Fix pyglet ImageData import
- Fix most pyrefly issues

### Changed
- Updates uv.lock
- Updates pys2clientprotocol to 1.0.2
- Migrates from s2clientprotocol to pys2cientprotocol
- Move renderer pyglet imports into TYPECHECKING check
- Update pyrefly

### Removed
- Remove instruction to copy s2clientprotocol
- Remove local s2clientprotocol .pyi files
- Removes unused import
- Remove duplicate and improve error messages
- Remove all pyre-ignore comments


## [7.1.2] - 2026-01-01

### Added
- Add maps cache to gh actions and squash by default
- Add map download script
- Add python 3.14
- Add s2clientprotocol folder to docker ci
- Add overloads for protocol._execute
- Add overloads for position
- Add typing to position.py
- Add type hints for various files
- Add type hints for python-sc2 related to protobuf types

### Fixed
- Fix download maps script
- Fix pillow and scipy dependency
- Fix distance_to and refactor hasattr to isinstance
- Fix type hints for color
- Fix annotation by importing from future
- Fix zerg cost
- Fix ruff issues
- Fix id_exists method

### Changed
- Remove test folder in CI to not include it in the pypi package
- Use download_with_retry function
- Unwrap for loop in download maps script
- Split up markers for scipy
- Remove 3.14 from Run testbots linux
- Update package markers for numpy for py3.14
- Update matplotlib
- Simplify typing for position.py
- Replace IntEnum with Enum and clean up
- Revert using typing.Self
- Improve typing in library files
- Improve typing on example bots
- Replace list with iterable
- Apply more type hints
- Adjust enums to be of type int


## [7.1.1] - 2025-07-21

### Added
- feat: support dual expansion locations
- feat: add `_cluster_center` method and improve resource group clustering logic
- test: add Persephone as map with odd expansion count
- test: add pickle files for preseason 2025 maps

### Fixed
- chore: fix type hints
- Fix https://github.com/BurnySc2/python-sc2/issues/223


## [7.0.6] - 2025-06-27

### Added
- Add missing Fleet Beacon tech requirement
- Add python 3.13 to CI for testbots
- Update generate_ids.py to add abilities with empty 'buttonname' in stableid.json
- Adds ActionObserverCameraMove.distance to proto, enabling wide zoom-out
- Adds ActionObserverCameraMove.distance for wider Observers zoom-out

### Fixed
- Fix https://github.com/BurnySc2/python-sc2/issues/191
- Fixes example observer file TypeError: Cannot set ... replay_path to PosixPath

### Changed
- Replace pyre with pyrefly
- Deduplicate function call '_distances_override_functions'
- Makes unit.tag be @cached_property
- make sc2_version accepted by old join and host methods
- Update README.md
- Update README discord links

### Removed
- Remove self.do() references
- Remove unused import
- Repairs ObserverAI by removing deprecated field usage and assigning random Race for player_id 0(zero)


## [7.0.4] - 2025-01-05

### Added
- Add view source code button
- Add debug ls all generated docs files and fix docs urls
- Add type hints to docs

### Fixed
- Fix top level package directory for package build command
- Fix package build
- Fix dict tests on linux
- Use poetry build system again, fix windows test
- Update dicts for patch 5.0.14

### Changed
- Change docs folder
- Replace sphinx rtd theme with sphinx book theme
- Update id.py files


## [7.0.2] - 2024-12-18

### Added
- Re-add needs field
- Add entrypoint to coverage ci
- Add multiple future annotations
- Add missing future annotations to fix py3.9
- Re-add union type to fix python3.9 and 3.13

### Fixed
- Fix project name and bump version to 7.0.3
- Fix token parameter
- Fix container name
- Optimize run docker shell script and fix setuptools
- Set PYTHONPATH to fix docker tests
- Fix pyre issues for test folder
- Fix pyre issues for examples folder
- Fix pyre issues in sc2 folder
- Fix docker-ci

### Changed
- Explicitly exclude license file from publish
- Remove license field
- Let build() accept None position again for upgrades or morphs
- Undo missing isinstance with pipe operator calls
- Undo isinstance change
- Automatically infer types
- Use typing from types instead of typing library
- Replace missing poetry entries with uv
- Remove cache from CI
- Replace poetry with uv

### Removed
- Remove cd


## [7.0.1] - 2024-11-22

### Added
- Add constraints for scipy
- Make numpy version more flexible and enable CI for python3.9 again

### Changed
- Update package versions


## [7.0.0] - 2024-10-28

### Changed
- Make changes resulting in drop of python3.9 in favor of python3.13 (#203)


## [6.6.0] - 2024-08-03

### Added
- Add baneling example bot
- Manually add morph to baneling back to dicts

### Fixed
- Fix pypi publish CI
- Fix ruff issues
- Apply ruff --select F --fix
- Apply ruff --select Q --fix
- Fix maps urls and use curl instead of wget
- test: updated upgrade tests for patch 5.0.13
- test: updated pickled map files for patch 5.0.13
- fix: correct ids for 5.0.13
- Update dicts to patch 5.0.13
- Update dicts to patch 5.0.12
- Update ids to patch 5.0.12

### Changed
- Bump minor version to 6.6.0
- Skip test function for macOS (#200)
- Install ruff and pyre
- Update packages
- regenerate dicts as was previously inaccurate
- style: run pre commit formatting hooks
- style: run pycln formatter
- style: run isort to format imports
- yapf formatting
- update ids to 5.0.13

### Removed
- Remove 'working-directory'
- Remove some pre commit entries


## [6.5.0] - 2023-11-30

### Added
- Update packages and enable python 3.12 (#186)

### Changed
- Update sphinx and sphinx-rtd-theme version
- Bump pypi version to 6.5.0


## [6.4.0] - 2023-08-03

### Added
- Add maps to test/generate_pickle_files_bot.py

### Fixed
- Fix pylint warnings

### Changed
- Bump pypi version to 6.4.0

### Removed
- Remove 'pylint disable W0719'


## [6.3.0] - 2023-07-14

### Added
- test: add pickled data for latest ladder maps

### Fixed
- fix: check if height is similar rather then exact between resources
- fix: terrain height check when calculating resource groups

### Changed
- style: yapf formatiing
- Remove codecov package and from CI


## [6.2.0] - 2023-04-05

### Added
- Add CREATION_ABILITY_FIX to fix exact_id errors on already_pending and add test
- Add __future__.annotations and update ids, add _missing_ to AbilityId Enum
- Skip 'Login to DockerHub' in PRs, add 'VERSION_NUMBER' as build arg, use 'squashed' docker image to run tests
- Add Point2.round() function

### Fixed
- Fix morph to baneling in dicts

### Changed
- Bump pypi version
- Release to pypi after tests were successful
- Remove 'townhall.is_facing(scv)'
- Update actions/checkout to v3 and setup-python to v4
- Start locations position rounding


## [6.1.1] - 2023-01-16

### Fixed
- Improve archon morph test and fix already_pending for archons


## [6.1.0] - 2023-01-13

### Changed
- Convert classes to dataclass (#148)

### Removed
- Remove "cached_property" from Units class
- Remove ".keys()" where possible


## [6.0.7] - 2023-01-06

### Added
- Update dependencies, add cache to CI
- Add python3.11 suppport (#154)

### Fixed
- Fix tests by updating packages

### Changed
- Bump pypi version
- Update README.md for Linux installation (#159)
- Set default client.game_step to 4

### Removed
- Remove unnecessary comments and print statements


## [6.0.6] - 2022-10-01

### Added
- Add _missing_ function for buff_id

### Fixed
- Fix buffid mistake

### Removed
- Remove rally abilities from combineable abilities


## [6.0.5] - 2022-09-22

### Added
- Add pickle files of new maps, update ids

### Fixed
- Fix map name in tests and bump version
- Fix Github Actions CI cache

### Changed
- Update README to recommend exporting environment variables


## [6.0.4] - 2022-06-17

### Added
- Add ONCREEP buff_id


## [6.0.3] - 2022-06-15

### Added
- Add codecov token
- Add '-a' parameter to coverage command
- Add codecov badge
- Add 'Upload coverage to Codecov'

### Fixed
- Remove class_cache type hint, fix CI

### Changed
- Disable cache on windows
- Reduce match duration for ramp wall bot in tests
- Improve code coverage
- Set fail_ci_if_error to false
- Increase timeout limit for radon
- Improve python file checks
- Make codecoverage always run
- Increase timeout limit
- Update packages, run code coverage inside docker


## [6.0.2] - 2022-05-28

### Added
- Add constraint protobuf = "<4.0.0"
- Add new python version test script
- Add more python versions to ci
- Add echo for debugging
- Add curly braces again where required
- Enable docker experimental features before running shell script

### Fixed
- Fix curly braces around global env variables
- Fix BUILD_ARGS
- Fix ci.yml env variables
- Fix ci.yml
- Remove env. prefix
- Fix tests, improve error logging

### Changed
- Use output of 'python --version' as cache key
- Use actions/cache@v3
- Update actions/setup-python version to 2
- Drop ${{}} around env variables where possible
- Separate docker image upload
- Move env argument
- Refactor using env or local variables
- Stretch Dockerfile to make it readable again, use experimental --squash flag in docker build process

### Removed
- Remove python beta release client
- Remove env variable from job level env


## [6.0.1] - 2022-05-23

### Added
- Add 'poetry config virtualenvs.create false'
- Add sphinx_rtd_theme import
- Add sphinx_rtd_theme to sphinx extensions
- Add on:pull_request to docker-ci.yml
- Add Dockerfile and update sphinx theme

### Fixed
- Fix docker build command

### Changed
- Update docstrings
- Update shell script and ci.yml
- Update Dockerfile and ci
- Restructure simulate_fight_scenario.py


## [6.0.0] - 2022-05-13

### Added
- Remove six, add replays for test
- Remove step_time_limit, simplify main.py, add verbose argument to clean function
- Add bot vs bot to test
- Add root folder to sys.path
- Add six library and move import in renderer.py
- Apply additional pylint fixes, add script to test all example bots, replace set with frozenset in some cases, apply functools.cached_property
- Add initial pylint fixes

### Fixed
- Fix cache for other OS on github actions
- Fix tests
- Replace print statements with loguru logger, fix formatting
- Fix missing workflow renaming
- Fix workflow name
- Apply pylint fixes to examples subfolders
- Attempt to debug why bot vs bot hangs after game completion
- Fix on_start
- Fix run testbots script

### Changed
- Test bots using multiple docker images for multiple python and sc2 versions
- Remove unused packages
- Separate workflow run_examples_bots
- Comment out bot vs bot in github actions, refactor _play_game_ai
- Use a_run_multiple_games_nokill
- Make code coverage a separate workflow
- Update packages
- Move more pyglet imports in renderer.py

### Removed
- Remove bat_files folder, update python 3.7 references to 3.8
- Remove helpers folder, separate internal bot_ai from BotAI class, merge distances.py into bot_ai_internal.py


## [5.0.15] - 2022-03-28

### Added
- Add adept shades example

### Fixed
- Fix protocol error when trying to save replay
- Fix https://github.com/BurnySc2/python-sc2/issues/127
- Update dictionaries and data.json to patch 5.0.9
- Updated all README examples, fixed imports
- Fixed the WorkerRushBot example in README

### Changed
- Update packages and bump version
- Update generate ids to use yapf instead of black formatter
- Update README.md

### Removed
- Removed imports from minor examples


## [5.0.13] - 2022-01-24

### Added
- Update packages and enable python 3.10 for tests
- Add new maps as pickle data for tests
- Re-enable test bots
- Add and apply pre-commit hook

### Fixed
- Fix build include files and bump version
- Fix BotAI import
- Fix test bots

### Changed
- Cache poetry packages
- typo
- unwanted buildings replaced with start locations
- simplify bootstrap
- singleiners
- simplify game end
- damage only supply depots
- use shorthand method
- sim
- imports
- Use pip install instead of poetry inside docker
- Create pyproject.toml, convert all pipenv commands to poetry
- Disable run_autotest_bot
- Bump pypi version
- Generate fresh bot objects when running tests

### Removed
- remove supply damage as not needed


## [5.0.12] - 2021-10-05

### Added
- Add patch 506 maps
- Add SC2 AI Arena Season 1 maps

### Changed
- Improve test_bot_ai by creating a clean object for test_bot_ai
- Updated readme for disabling wsl detect
- Allow disabling WSL detection with an environment variable


## [5.0.11] - 2021-05-22

### Added
- Add base_build to ObserverAI

### Fixed
- Fix https://github.com/BurnySc2/python-sc2/issues/86
- Correct morph_cost for morphed units

### Changed
- Change back observer_ai.py
- Restore unit_tag function signature
- Update tests
- Update dependencies (especially s2protocol to 5.0.7)
- Redirect subprocess stderr to subprocess.DEVNULL (suppress error/warning messages)
- Update dependencies

### Removed
- Attempt to remove projectiles from on_unit_destroyed Also change signature of 'on_unit_destroyed' function: Argument is now a Unit (from previous frame) instead of unit_tag


## [5.0.10] - 2021-03-14

### Fixed
- Fix for issue #89


## [5.0.9] - 2021-02-28

### Changed
- Update packages and bump version


## [5.0.8] - 2021-02-18

### Fixed
- Fix type hint for 'get_terrain_z_height'
- Remove Point2 type hint from several debug draws


## [5.0.7] - 2021-02-17

### Added
- Add Python3.9 to tests, update packages
- Fix https://github.com/BurnySc2/python-sc2/issues/83 and add DeprecationWarnings to can_place()
- Add sensor tower to TERRAN_STRUCTURES_REQUIRE_SCV
- Add self.base_build variable to BotAI and Unit class, simplify Unit.is_snapshot for new game versions

### Fixed
- Fix find_placement

### Changed
- Update README.md

### Removed
- Update data.json to remove 'durable materials' upgrade research
- Remove commented out code from units.py


## [5.0.6] - 2020-11-25

### Added
- [WSL-SUPPORT] Add WSL version autodetect and warn
- [WSL-SUPPORT] Add special start/stop code for WSL
- [WSL-SUPPORT] Move wsl stuff to wsl.py
- [WSL-SUPPORT] Update README.md
- [WSL-SUPPORT] Allow env config of SC2Process ports
- [WSL-SUPPORT] Add WSL path mangling support
- [WSL-SUPPORT] Add paths for WSL1 and WSL2

### Fixed
- Fix https://github.com/BurnySc2/python-sc2/issues/82
- Fixed links to aiarena.net

### Changed
- Replace ai-arena.net with aiarena.net
- Re-adjust ramp wall points


## [5.0.5] - 2020-11-20

### Added
- Add WorkerStackBot to give an example on how to assign workers per mineral patch
- Add 'typing-extensions' to fix aiohttp imports in python 3.8
- Add draw expansion locations for ramp_wall bot

### Fixed
- Fix (Golden Wall) and improve expansion finding

### Changed
- Increase SC2 start-timeout limit from 1 to 3 minutes
- Update pipenv dependencies


## [5.0.4] - 2020-11-05

### Added
- Add hydralisk upgrade research for hydralisk_push.py
- Add a guide on how to use Docker to run bots headless
- Add warning (once) when wrong target was given for a specific ability (e.g. Unit instead of expected Point2 as target for ravager bile)
- Add comments to queries test
- Add more time in between tests, add offset to creep tumors
- Add queries_test_bot to test can_place function

### Fixed
- Fix building requirement for spore crawler
- Fix the issue of game being launched twice without asking for the user input
- Fix https://github.com/BurnySc2/python-sc2/issues/68 and other debug draw functions that accept Unit or Point2 as argument

### Changed
- optimize upper2_for_ramp_wall
- Disable test 'real_time_worker_production.py'
- Replace list with set


## [5.0.3] - 2020-09-14

### Fixed
- Fix structure_type_build_progress(), related issue: https://github.com/BurnySc2/python-sc2/issues/65


## [5.0.2] - 2020-09-06

### Added
- Add battery-overcharge testbot
- new ids for 5.0.3

### Changed
- Update dependencies and bump version
- Update sc2/dicts


## [5.0.1] - 2020-08-30

### Added
- Add a repository link to the documentation, add a Cost class description

### Fixed
- Fix https://github.com/BurnySc2/python-sc2/issues/61
- Fix https://github.com/BurnySc2/python-sc2/issues/62 by explicitly returning python bool


## [5.0.0] - 2020-08-02

### Added
- Add 'right' and 'top' property to rectangle class
- Add --RealTime argument for competetive bot example, add/fix realtime arg for BotProcess and Proxy
- Add package importlib_metadata to requirements
- Implement more features
- Add cyclomatic complexity report to github actions
- Implement vs-non-python bots

### Fixed
- Fix ids for SC2 version 5.0
- fix pip
- Fix crashes on linux
- fix None crash
- Fix stdout issues and leaving when opponent crashes
- Attempt to fix 'prevent_double_actions'

### Changed
- Use sharpy's --RealTime argparse argument
- Simplify 'get_runner_args' for WINE
- Update competitive example for vsComputer
- Start sc2 at the same time on windows, sequentially on linux
- Make use of loguru logger, set realtime to False by default, make it work on linux
- Update ids to sc2 version 4.12
- run multiple games


## [4.11.16] - 2020-06-30

### Added
- Improve description on 'add_on_position'
- Add pickle files, remove blood boil
- Add addon_place option in find_placement

### Fixed
- Fix small things
- Fix tests
- Fix _initialize_variables and _prepare_units functions

### Changed
- Bump pypi version
- Update dict of units and their equivalent types
- Shorten and document code
- Update AI Arena maps link and improve map download instructions and formatting.
- Move expansion finding and resource amount tests to "test_pickled_ramp.py" so that it can be tested on each map, and not just a single random map
- rewritten in proper english
- modify doc string of `surplus_harvesters`
- combine statements


## [4.11.15] - 2020-04-29

### Fixed
- Fix typo in documentation
- Fix exit code 2 being returned after game has already ended

### Changed
- Change weapon_ready property to weapon_cooldown ==0


## [4.11.14] - 2020-04-08

### Changed
- bot_ai.py changes
- unit.py changes
- client.py changes
- Remove unused packages, update README.md


## [4.11.13] - 2020-04-07

### Added
- Add 'wineserver kill' command for games that are run through linux and wine
- Add placeholders to self.all_units to enable distance calculation
- Enable placeholders and a bot that does not use can_place query to expand everywhere
- Add more queens to zerg rush bot
- Add type hints to terran and protoss example bots
- Add comments to zerg example bots
- Add DeprecationWarning for self.do(). Set 'self.unit_command_uses_self_do = False' by default
- Add __iter__ function to generate suggestions (IDE) when looping over Units

### Fixed
- Fix expansion_locations_dict
- Fix hydra and BC bots
- Fix self.build, self.train, self.research to use self.do but suppress warning Fix type hints for unit.py
- Fix len for expiring dict

### Changed
- Improve self.research()
- Increase timeout limit
- Redo expansion_locations property
- Update terran bots with comments
- Simplify expiring dict repr function
- Disable len for expiring dict

### Removed
- Undo repr changes in expiring dict, remove max_len because there is no simple way of removing the oldest entry


## [4.11.12] - 2020-03-21

### Added
- Change can_place function to accept multiple locations (and return a list of bools), while still keeping it downward compatible (able to pass just one location and return one bool) Add function '_query_building_placement_fast' which returns bools instead of ActionResult
- Add pip packages cchardet and aiodns for aiohttp
- Add more docstring info to movement_speed

### Fixed
- Fix type hint in dicts

### Changed
- Github actions: increase timeout to 30 minutes
- Get rid of Point3 in bot_ai.py


## [4.11.11] - 2020-03-13

### Added
- Add worker production bot to test if more than one probe ever gets queued
- Add return statements to unit commands, which return bool
- Add example bot for worker split in realtime=True
- Add "mkdir docs" command
- Add more asserts on watching replays

### Fixed
- Fix documentation for self.do()
- Fix ProtocolError for realtime=True and on_end() https://github.com/BurnySc2/python-sc2/issues/45
- Fix tests, improve description in on_unit_died_event
- Fix structures_without_construction_SCVs
- Fix arcade and show_debug bots

### Changed
- Put worker production test bot to 'self.client.game_step = 1'
- Increment supply_used back to >=199
- Increase timeout_time
- Remove "rm -r docs"
- Remove /docs folder as it gets recreated and redeployed by github-actions
- Improve indexing in distance calculation functions
- Move id-generation file to sc2 folder

### Removed
- Remove "self.do", call it directly from unit.py
- `self.known_enemy_units` is deprecated,


## [4.11.10] - 2020-02-26

### Added
- Add atomicwrites to fix tests (pytest) on windows
- Fix tests - add exception for armory armor plating
- Fix upgrades in dicts Add "required_upgrade" in dict unit_research_abilities.py
- add speed calculation
- Update example competitive ladderbots.json
- Add documentation for config options that were previously removed from the example bot.
- Add missing close bracket
- Enable show_burrowed_shadows

### Fixed
- fix some values
- Fix introduction example

### Changed
- Allow disabling of fog of war
- Improve calculate_speed() function by replacing if else with dicts
- Improve competitive example README
- Reorder bot method definitions to mimic the order they will be called in.
- Rename the bot class to minimise the need to further rename after using the template.
- Update README
- Clean out the example competitive bot in order to use it as a standard clean template.
- Brand the AI Arena example bot as a generic "competitive" example bot.
- Update readme for linux with wine

### Removed
- Remove introduction.rst duplicate


## [4.11.9] - 2019-12-29

### Added
- Add footprint_radius to Unit

### Fixed
- Fix roach warren upgrades

### Changed
- Some docstring reformatting + some pylint warning silencing and do maintainer requested changes
- Suppress numpy warnings


## [4.11.8] - 2019-12-16

### Fixed
- Fix can_attack_both

### Changed
- make using self.build() possible for gas buildings


## [4.11.6] - 2019-12-12

### Added
- Add unit.distance_to_squared()
- Remove supply depot drop from constants, add distance method 3 without asserts
- Add DeprecationWarning to self.larva_count
- Add assert to unit.build and unit.build_gas
- Add smart command to unit.py

### Fixed
- Attempt to fix structure_type_build_progress once more

### Changed
- Limit pypi and github pages release to push
- Don't do actions if list of actions is empty
- Update documentation text file
- Replace bot.larva_count with property instead of data from proto


## [4.11.5] - 2019-12-10

### Added
- Add github actions status badge
- Add ladderbots.json to example_bot
- Add raw_affects_selection and example __init__ bot function

### Fixed
- Fix badge link

### Removed
- Remove print statement from library


## [4.11.3] - 2019-12-09

### Fixed
- Fix tech_requirement_progress and structure_type_build_progress, change f-strings to format strings
- Fix BC and bunker calculation
- Fix damage calculation for targets that are not completed / ready

### Changed
- Removing asserts for some Units filter functions
- Convert from travis to GitHub actions (#35)
- Update readme and comments
- Update README.md


## [4.11.2] - 2019-11-30

### Added
- Add upgrade test bot and separate combat test bot
- Add autotest_bot test: research all upgrades, fix upgrade dicts
- Enable linux test bot again
- Add function worker_en_route_to_build and property structures_without_construction_SCVs Try to fix and make already_pending_upgrade simpler, fix Unit.research
- Update dicts and data.json, add TERRAN_STRUCTURES_REQUIRE_SCV to constants

### Fixed
- Disable autotest bot on docker as long as linux sc2 client balance patch is different from windows sc2 client
- Fix structure_type_build_progress and tech_requirement_progress
- Fix unit_trained_from dict for orbital and PF

### Changed
- Downgrade docker to 3.7
- Turn off damage calculation test
- Update documentation

### Removed
- Remove numba


## [4.11.1] - 2019-11-28

### Added
- Update a lot of minor changes, improve generate_pickle_files_bot, add batch scripts folder
- Add travis build status to README.md


## [0.12.12] - 2019-11-28

### Added
- Update a lot of minor changes, improve generate_pickle_files_bot, add batch scripts folder
- Add travis build status to README.md
- Improve cache, add another cache decorator that does not copy mutables
- Add draw_placement_grid function to ramp wall bot

### Changed
- Update upgrades and abilities for 4.11
- Update ids for SC2 version 4.11


## [0.12.10] - 2019-11-26

### Added
- Add weapon speed and weapon range to Unit.calculate_damage_vs_target(), simplify tests
- Add unit.game_loop and unit.is_memory properties as suggested by DrInfy
- Add functions and properties from DrInfy's fork
- Add _advance_steps() function for testing, add tests for Unit.calculate_damage_vs_target() function
- Add 'self.attack_upgrade_level' to damage per attack
- Add 'calculate_damage_vs_target' Unit function
- Add monkeytype to dev packages, add archon to 'calculate_cost'

### Fixed
- Fix research requirements for spire upgrades
- Fix calculate_damage_vs_target for battlecruiser and vs colossus, units affected by guardian shield and anti armor missile
- Fix tests
- Fix cost test

### Changed
- Update data.json, generate_dicts script and /sc2/dicts
- Revert unit_command.py
- Move "self.queue" to the end in "combining_tuple"


## [0.12.9] - 2019-11-20

### Added
- Add temporary fix for is_snapshot and is_visibile
- Add apm to score.py
- Add 'units_created', a Counter to keep track of how many units and structures were produced Change 'on_building_construction_complete' event to include the starting townhall
- Add on_unit_type_changed event
- Add amount of damage taken to on_unit_took_damage event
- Add free units to tests to calculate_unit_value function
- Add calculate_unit_value function
- Add length and normalized property to Point2 to be able to act as a vector
- Add temporary fix for linux client to include rich geysirs (e.g. EXTRACTORRICH) in gas_buildings
- Add on_unit_took_damage, on_enemy_unit_entered_vision, on_enemy_unit_left_vision events
- Add multiplication with scalar to Cost class
- Improve and add comments to ExpiringDict
- Add expiring dict based on self.state.game_loop

### Fixed
- Fix docstring for bot_ai.on_start and unit.is_active
- Fix tests

### Changed
- Change Union[int, float] to 'float'
- Update maps on README.md


## [0.12.7] - 2019-11-05

### Added
- Add has_techlab and has_reactor to unit.py
- Add AI Arena example bot
- Add support for running in different wine versions
- Add examples/watch_replay.py
- Add matplotlib to dev pipenv packages
- Add a "build_gas" function to unit.py
- Add "Unit" as possible target to the move command

### Fixed
- Fix ids and generate_id_constants_from_stabeleid, bump version
- Fix typo, improve comment description
- Fix documentation - Change self.units to self.structures
- Fix variable name
- Fix can_afford shortcut
- Fix build command in unit.py

### Changed
- Short cut can_afford

### Removed
- Remove unnecessary variable


## [0.12.3] - 2019-10-16

### Added
- Add support for playing replays
- Enable python 3.8 tests, fix onebase_battlecruiser
- Roll back deprecation fix, add note for future
- Add is_facing function
- Add cdist and python's math.hypot() function as distance calculation methods which can be selected once at game start by putting "self.distance_calculation_method = 0" (or 1 or 2) in your __init__ bot class
- Add step_time property to measure bot performance
- Improve performance on drawing the same static things over and over Add simple drawing example for most debug draw objects in ramp_wall bot
- Add code coverage comment
- Add code coverage
- Add 'in_map_bounds' function to bot_ai

### Fixed
- Fix gas_buildings to include rich gas buildings
- Fix generate_docs.bat command to remove docs folder before generating, exclude examples folder from setup.py
- Fix deprecation warning
- Fix can_afford function when in negative supply
- Fix creep pixelmap
- Fix typo
- Fix opponent_id which was set to None even though it was already set to a string value
- Fix expand_now for when all expansions are taken or all of them are mined out
- Remove coverage because it is not working for python 3.7 Disable python 3.8 test to speed up travis Fix test

### Changed
- Improve proxy rax example
- Improve onebase bc example
- Improve mass reaper example
- use precalculated number
- Code cleanup :D
- Update docs
- Change argument type hints from list or set to iterable
- Force cache expansion location before first step
- Specify python version 3.7


## [0.12.2] - 2019-09-12

### Added
- Add necessary script line
- Add test to morph 400 lings to banes in one frame
- Add test for self.train()

### Fixed
- Fix grouping of abilities


## [0.12.0] - 2019-09-11

### Added
- Add pypi to allowed failures
- Add script to automatically release to PYPI (#19)
- Add season 8 AI ladder map pickle files to tests
- Fix mineral walls: dont group MineralField450 for expansion minerals. Add MINERALFIELDOPAQUE and MINERALFIELDOPAQUE900 in constants
- Add game_loop parameter when receiving observation, this should fix a couple realtime=True bugs
- Change assert statement, enable test bot again to run with the linux starcraft version 4.10
- Add sc2_version to run_game parameter to be able to launch an older version of the SC2 Client Example can be found in examples\terran\cyclone_push.py TODO: The versions.json needs to be automatically updated by running a script
- Add init file so that pip install command also copies the dicts folder
- Add generic abilities to tests and show that they are bugged
- Add documentation and examples to Units filters
- Add protoss wall to tests
- Add variables to pixelmap to be able to copy it
- add protoss wall, prevent crash on cleanup, use explicit error in __mul__
- Add introduction to the library python-sc2
- Add generic redirect abilities which may help debug ability cost of upgrades
- Add unit and tech alias dicts
- Add realtime=True indicator variable if game is played in realtime mode
- Add comments, change '"Unit"' to 'Unit' in type annotation
- Add type annotation
- Add custom tech requirement because the on in the API does not work reliably (thor and ghost are not correct)
- Update docstrings, add "self._unit_tags_received_action" to prevent multiple actions issued to the same larva / worker / train structure
- Add generalized research bot_ai function
- Add example bot using new self.train and self.tech_requirement_progress functions
- Add all unit abilities
- Add dentosal's tech tree, add dicts with unit abilities
- Add dicts and generator bot
- Add params for init functions
- Add input params to several functions
- Add sphinx to pipfile
- Add documentation branch
- Add ravager bile test
- Add reaper grenade effect test to test bot
- Fix and add type hints
- Add after_step function that is called from main.py
- Fix debug draw, add numpy to cache every frame .copy() list
- Add target_melee_in_range for scv repair
- Add todo: larva count reduction
- Add __add__ for units, fix issue events
- add workers, townhalls and gas buildings in prepare units
- Add numpy array creation benchmark
- Add pdist calculation to tests
- Add scipy, scikit-image, pyytest-benchmark, numba Add distance calculation benchmarks
- Update expansionlocations again, add dump data, unit.can_be_attacked
- Fix pickle generator, add missing pickle file 16bit
- Fix tests for new ramps and vision blocker function
- Add resource ratio and fix crash on no minerals on map
- Fix proper termination on game end, fix on_end trigger on ladder server
- Add terran to z height function, fix typo, fix test
- Add note to is_visible, is_revealed, attack/armor/shield upgrades, buff time to unit. Add alert check, use try/except in prevent double actions
- Add is_transforming and can_attack_both
- Add add self.response_observation for tests
- Add devtools, add watchtowers, speed up unit loop in game state
- Add rounded for point2 and 3, remove from pointlike
- Fix pixelmaps, ramp walls, and tests. Update pickle files with new proto data
- Start fixing bugs with new client update
- Add tweakimp's expansion locations fix
- Add more tests that use pickle files
- Fix TypeError log on game end, add try execpt blocks to cut isinstance calls, change point equality to be exact
- Add example usages
- Speed up can_place and already_pending_upgrade, add EffectData __repr__ , add Point2 __hash__, improve Pointlike __eq__, improve unit __hash__ and __eq__
- Add Unit.is_using_ability
- Add deprecation note for gamedata change
- Add autocast toggle function
- Add debug text example
- Add option for fullscreen windows
- Addition for Cost objects
- Add Pointlike.is_closer_than(dist, pos)
- Add AIBuilds
- Add idle worker count, army_count, warp_gate_count, larva_count to botai
- Add zergling for exception
- Add is_detector property
- Add alerts, and worker/army supply
- Fix ramp bug on map Acolyte and add cache for ramp points
- Remove .rounded in self.build function, Add quick_save and quick_load client.py functions
- Add on_upgrade_complete event
- Add on_start_async method (changing on_start to async may confuse many authors) and reorganize main.py structure Now at on_start and on_start_async, game_data and game_info and game_state (self.state) information will be available
- Add debug (cheat) function
- Add more caching and update comments
- Adds 'on_building_construction_started' event hook to the bot.
- Add more time limit options
- Add bonus damage
- unit overhaul, inherit from passengerunit and add comments
- Add ressources selection
- add UnitTypeId import
- Use ressource ids, add TODO
- Add random_seed parameter
- Add WineLinux platform and SC2PF envvar to set the platform
- Add can_attack property (#185)
- Add a working RGB renderer on Linux
- Add GameData parsing optimization
- Add resource height comparison for resource groups
- Add same tech and same unit filter
- Add minor performance improvements
- Add mypy type checking
- Add Point2 vector functions and operators
- Improve distance calculation and add sorted_by_distance_to
- Add repair and is_repairing
- Fix Techlab and Reactor cost, add mypy type checking
- Add Blizzard's EULA agreement
- Add is_construction_scv property
- Add arcade map bot example
- Add simple PixelMap info getters
- Add returning and collecting properties / filters
- Add missing await statement on issue_events
- Add surrender hint
- Fix missing upgrade by adding an index to enum name
- Add target_in_range test
- Add target type enum
- Add tests for position.py, unit.py and units.py
- Add method on_end
- Add can_feed to can_afford check
- Add "not"
- Add the last missing data to score.py
- Add opponent_id to bot class for sc2ai ladder
- Add PassengerUnit to support cargo units
- Add "is_psionic" property (#111)
- Add important test for do_actions() (#102)
- Add headless linux tests to travis CI testing (#101)
- Add already_pending for upgrades
- Add comments and mypy type checking (#95)
- Add enemy_race and time property to bot_ai.py, improve comments in client.py
- Add score, mypy type checking and more (#89)
- Add missing properties of ResponseObservarion to game_state.py
- Add gitignore PyCharm project folder
- Add on_unit_created and on_unit_destroyed and on_building_construction_complete
- Add ignore_resource_requirements parameter to be used in available abilities query
- Add different functions to print debug text
- Add simplified debug_text to client.py
- Add travis CI unittests (#88)
- Add closest_distance_to and a few asserts
- Fix to surplus_havesters, added more unit info
- Add a bot example that uses the newly implemented attributes and functions
- Add debug spawn unit function
- Add check if unit can cast an ability - energy cost and ability range
- Add dead unit events, effects and upgrades
- Fix to pixel map (y position was reversed) Added visibility and creep to self.state
- Fix crash when enemy in sensor tower range + support destructible rocksu
- Add furthest_to filter mainly for units stutter stepping backwards
- Add Units.further_than filter
- Add resource subtraction on action execute attempt
- Add function for multiple actions at once (but without can_afford)
- Add weapon_cooldown to Unit attributes
- Add furthest away method
- Add gathering and center of units
- Add checks if Unit can attack ground and/or air
- Implement fast reloading (fixes #40)
- Add Units filters that use the new Unit attributes
- Added a few more attributes
- Add missing ability (212) to ability_id
- Add warning about BotAI.distribute_workers slowness
- Add more examples
- Add ramp support
- Add Broodlord example for zerg
- Also enable verbose logging for sc2 process
- Add initial ramp map
- Add modification operations to control groups
- Add control group helper
- Add some unit tests for directions
- Add an option to limit game max length
- Add game_loop to state to indicate elapsed game time
- Added a note about sc2-bot-match-runner repository
- Warpgate support  (#28)
- Add new terran example
- Add a convenience method to expand to the nearest unoccupied expansion
- Add logging for replay save operation
- Add possibility to detect add ons
- Add a slow bot to test timeout feature
- Add JSON serialization support for portconfig
- Add three base void ray strategy example
- Add methods for expanding to new bases
- Add some new fields to the unit (from the last API update)
- Add wiki link to the readme
- Add support for sending chat messages
- Add bot vs bot example
- Add automatic tests
- Add leave command to cleanly exit games
- Add TvZ Human vs AI example
- Add portconfig class
- Add repr method for cost
- Add possibility to run multiple clients
- Add proxy rax example for terran
- Add id autogeneration script and result files
- Add debug text drawing
- Add zerg(ling) rush example
- Add signal handler to always clean up after the game ends
- Add group operations
- Add non-exact name comparison
- Add new example: cannon rush
- Update examples to match the new syntax
- Add unit commands and selectors
- Add mention about releases and tags
- Rename to "sc2", add setup.py
- Add worker rush and required code

### Fixed
- Fix travis test script
- Try to fix: 3670 is not a valid AbilityId
- Fix "on_building_construction_started" event
- Fix broodlord example accidental typo
- Fix example bots errors
- Fix can_afford for zerg units created from larva
- Fix imports and typo Fix a TODO: reduce larva count by 1 in self.do if unit was trained from larva
- Fix protoss wall on honorgrounds LE
- Fix typos
- Fix "on_unit_created" event when workers are leaving the gas structure
- Fix tests
- Fix logger score in main.py
- Fix get_available_abilities example
- Fix TypeError on game end
- Fix type hints and autotest_bot
- Fix description
- Fix ramp wall bot
- Fix protoss example bots
- Fix distance_to in unit.py
- Fix test and test generation files, update pickle files with 4.9.0 data
- Fix awaits
- Fix distances dict to use tag instead of position_tuples key
- Fix ids for 4.9.0, fix imports, get ramp wall bot to run, fix basic issues
- Fix distances_units assert
- Fix ramp finding code, improve tests, compress pickle files with lzma
- Reduce minimum amount of expansions to 10 (fix for bel'shir vestige)
- Fix .travis.yml
- Remove old_distance_to from test, fix blipunits in gamestate
- fix last typos
- Fix wrong variables and comparison in distribute workers
- Fix closest and furthest in botai and self.unit in game state
- Fix distribute workers, only get units objects in game state if we need them
- Fix game state alliance bug
- Fix line in .travis.yml
- Fix expansion locations height errors
- Fix pointlike __eq__
- Fixes bad import in renderer.py
- Also show position in debug example
- Workaround for incorrectly set lurker morph ability
- Fix some types, clean game step
- Fix ability crash
- Try to fix enemy race crash, improve cache
- Workaround for zerg supply rounding bug
- Fix map area, Fix pixelmap getter and setter
- Make _find_groups a generator,format imports,fix crash in can_cast
- Fix property_cache_once_per_frame
- Use more _distance_squared, fix empty units call crash
- Fix bot_ai.py
- Fix units.py
- Fix bug in expand_now when location=None
- Fix main.py
- Fix crash when a realtime game ends
- Fix dead units, get complete game data
- Fix crash on game over race condition
- Fix difficulty
- Fix issue when timeout during ws send causes out-of-sync messaging
- Fix missing cache, improve some assert statements
- FIx Human string issue
- fixC
- fixB
- Fix debug_text_simple
- Improve asserts and fix Units.take function
- Fix weapons in unit, improve game state init, cache typeid
- Fix unit object class name
- Fix import crash
- Fix crash
- Fix list initialization
- Fix indent
- Tweakimp patch (#186)
- Fix move_camera (#184)
- Update unit_typeid to fix Viking enum
- Fixed a typo
- Fix Para Site ramp crash
- Hackfix: Improve ramp code speed
- Fix a bug that prevents making overlord on negative supply
- Fix issues with distribute_workers
- Fix resource spread threshold and some calculation speedup
- Fix minor issues
- Fix center function for type checking
- Fix Point2 vector functions and operators
- Fix indention
- Fix __repr__()
- Fix is_visible()
- Fix another typo
- Fix typo
- Fix expansion position in threebase_voidray example.
- Fix ramp bug on ParaSite SC2 map
- Fix expand_now()
- Fix testbot file name
- Make to_debug_color accept lists and tuples as arguments
- Fix mypy type check
- Fix cost of zerg structures and building morph cost (#98)
- Fix debug_create_unit
- Hotfix query_available_abilities (#94)
- Fix main ramp walling (#92)
- Fix typo in "AbilityId" name
- Fix issues created by merges
- Fix formatting
- Fix error occurred after removing resonseObservation from GameState
- Fix misplaced bracket
- Fixes and improvements
- Fix missing self
- Fix e2e slow test suite
- Fix typo in control_group.py
- Fix center property
- Fix a bug for pixel map on non-square maps
- Fix and polish to effect data
- Fix "center of units"
- Fix moving/attacking/gathering
- Fixed typo in control_group.py
- Fix a crash when game ends one step before the results are available
- Fix some names and paths in examples
- Fix command to start cannon_rush example
- Properly warn about incorrect map path, fixes #12
- Fix couple of calls to Pointlike.distance
- Fix expansion location discovery
- Fix gametime limit for computer vs human games
- Fix resigning on bot crash
- Fix voidray example
- Fix command center selection in example
- Fix realtime argument
- Fixes #13
- Fix the case when Paths.CWD is None
- Replace base_dir to self.BASE to fix unresolved variable
- Fix executable paths on Linux
- Fix unawaited call in the cannon rush example
- Fix small consistency issues
- Typofix
- Fix exit-crash bugs
- Fix subpackage imports
- Fix cannon rush bot
- Fix singleplayer
- Remove redundant debug prints
- Fix an issue when joining as observer

### Changed
- Update install instruction
- Indent release script
- Update install command in README.md
- Update README.md
- Update arcade bot to make it compatible with this fork
- Change self.state.visibility to non-mirrored
- Undo changes, change Dockerfile to use version 'sc2_4.10'
- Comment out 'assert self.id != 0'
- Make testbot uninstall local python-sc2 installation
- Make testbot use map Acropolis
- Turn versions.json to versions.py file
- Comment out benchmark tests
- Remove --benchmark-compare
- Apply Black formatter
- Simplify calculate_cost function
- Move ramp testing code into a separate file to speed up tests
- Revert await distribute_workers, vespene_geysers to vespene_geyser
- Update documentation
- Make use of tech requirement from constants.py in bot_ai train function
- Change defaultdict return value to UnitTypeId instead of None
- Sort output dicts in sc2/dicts/ using OrderedDict and sorted set repr function
- Update docstring with examples to be displayed with sphinx
- Update position.py
- Change docs theme to classic
- Create redirect html file
- Use alabaster theme instead
- Set theme jekyll-theme-cayman
- use generator in distribute workers
- Move property testing from autotest_bot to test_pickled_data
- Make forcefield, kd8charge and parasitic bomb dummy effects
- Update protoss examples with comments
- Change ramp wall bot
- Remove scikit and sklearn from requirements
- Change tests to test expansion amount
- initialize bot ai variables before first step
- Make ramp_wall bot use bot_ai.get_terrain_z_height()
- Remove numba error and requirement
- Rename geysers to gas_buildings, splits units into units and structures
- Initial upload of distance calculation rework
- Apply formatter
- Revert changes
- Unignore compressed pickle test files
- Organize .gitignore
- Ignore pickle data
- Dont cache proto information, precalculate enums of properties
- Change walls for impossible ramps (HonorgroundsLE) so that they return None or empty set instead of crashing the game
- Update bot_ai.py
- Use isdisjoint in buff checks, find vision blockers in game info
- Increase resource threshold for automaton middle bases
- Dont use huge numbers in tests, set epsilon for distance tests
- Speed up resource buffs and unit creation in game state
- Prevent key error in _find_groups
- Use math.hypot for distance calculation
- Remove test file
- Update distribute_workers
- remove alert tests
- Dont run autotestbot
- Roll back to epsilon difference on position __eq__
- Remove test_positions from autotest_bot
- Update expansion locations
- Change directory name
- Update tests with Unit and Units, change cache so it is bot-based not function-based
- Change logger to info
- Apply Black
- Update pipfile
- Shortcut is_using_ability if no orders
- Numpy entered the room.
- Use is_using_ability for more things
- Allow passing a set of abilities to is_using_ability
- Update autotest_bot.py
- Revert autotest formatting
- Improve double actions
- Prevent double actions
- Update warning and ids
- Update ids
- Improve upper and lower ramp loops
- Roll back property_cache_once_per_frame
- Update ids and their generator
- improve select_build_worker
- Improve actions and bot_ai
- Speed up client, bot_ai and game_state
- Don't include enemy_race when running on a single player map
- Filter out unavailable abilities
- Update Dockerfile using SC2 client version 4.7.1
- return the line of the occurrence and simplify it a bit
- Trailing whitespace
- Use generators and dont use game_data where we dont need it
- Use do_actions() instead of do() in WorkerRushBot
- Update unit.py
- Rewrite unit.py, clean unitcommand
- comment out test 5
- Test if test completes without chat
- Improve upper and lower in Ramp
- BUmp version
- Ignore closed connections in response to quit requests
- Use comprehension, squared distance, faster ramps
- Revert "Merge branch 'develop' into master"
- Allow setting player names
- Update gitignore
- Log player scores
- Remerge Burnys commits
- rollback1
- Set default of already_pending to all_units=True to always include morphing units (e.g. morphing from hatch to lair)
- Stop counting terran structures twice in already_pending function
- Update comments and allow Unit and Units to be allowed for several commands
- Clear sliding window on timeout penalty
- Inform bot about it's time budget with it's limited
- Update game_info
- Update IDs
- Update pixel_map.py
- Clean units.py
- Update units.py
- Update cache.py
- Update client.py
- Update PixelMap
- Update more
- Update game_state.py
- Improve expansion location even further
- current status
- Do not use same unit multiple times in one action
- Stop expand if no more places for expanding
- Update README.md (#182)
- Only check structures for building completion
- Update unit.py (#172)
- update
- Improve expansion location (#167)
- Relocate the game_info.find_ramps() call
- Import bisect
- Find point clusters during ramp search faster
- Load abilities faster
- Don't crash on expand_now when no townhalls are left
- Build a list of actions in distribute_workers
- Do not exit when action cannot be afforded, just log a warning
- ExecuteInfo.txt parsing
- Improve expansion_location
- Revert some changes
- Change list to set
- Change if else to dict
- Make events async
- Include unit radius in target_in_range function
- Update to version 0.9.0
- Change query_available_abilities to allow multiple per call requests
- Break some ramp code
- Update Pipfile
- Update README
- Upgrade to Python 3.7 and Pipenv
- Manually change effects because effect_id.py doesnt seem to be complete
- Remove accidental "not" in the units.gathering property
- Do a minor change to Unit.order_target
- Tweak the error message
- Also look for map files in the Map root directory.
- Use 2d positions by default
- Speed up warpgate example a bit
- Organize examples directories
- Update README.md with info on getting started (#35)
- Revert some breaking changes
- Tweak EXPANSION_GAP_THRESHOLD
- Improve BotAI.already_pending
- Update .gitignore
- Catch and log errors in BotAI.on_step
- Clarification for map locations
- Use `stableid.json` to generate ID enums (#24)
- `Unit.has_buff` and `BotAI.get_available_abilities(unit)` (#25)
- `BotAI.already_pending` enhancement (#21)
- `BotAI.distribute_workers` convenience method (#20)
- Log player id before game starts
- `BotAI.can_afford` result wrapper (#23)
- Rename expand_to_nearest to expand_now for conciseness
- Do expansion occupation checking first before querying pathing
- Directly return value instead of assigning to an unused variable
- Tweak `next_expansion` identification to ignore locations with nearby town halls
- Allow more fine-grained control on how building placement should be done
- Invoke str() on paths during _launch()
- Allow using save_replay_as in _join_game when called directly
- Lazily loads paths to allow importing the library even if SC2 isn't installed
- Use relative path for maps
- Update data ids
- Improve logging and handling of closed connections
- Improve proxy rax example
- Allow setting per-step timeout for BotAI
- Set up logger
- Allow running clients on different processes
- Allow bots without AI object for external games
- Play against Terran instead of Zerg in examples
- Allow custom hostname and port for sc2process websocket
- Use generic names in the worker rush example
- Allow saving replays
- Ignore .cache folder
- Improve resource cost calculations
- Eliminate the "game already ended" error
- Update examples to match library changes
- Update to match latest API changes
- Make examples importable
- Polish README.md
- Rewrite selection system to use constants instead of strings
- Properly quit from the game
- Impl repr
- Prepare with vespenen gas count too
- Allow targeting both units and positions
- Update readme
- Remove dependency "vectors"
- Allow returning None from on_step method
- Update description
- Testing publishing at PyPITest
- Require Python 3.6+
- Use github releases
- Prepare for pypi release
- Separate player logic from communication logic
- Initial, niminal useful version
- Initial commit

### Removed
- Remove realtime_game_loop variable
- Remove unnecessary assert
- Update pathinggrid every frame, use try except in unit._weapons, remove unnecessary isinstance calls
- Remove comments
- Remove offset overwrite
- Update ids, remove unneccessary property caches
- Clarify deprecation notice
- deprecate warning for duplicated functions
- Remove bool type check
- Delete settings.json
- Remove isinstance(p, Unit) call
- Remove assert in prepare_first_step()
- Remove cargo_size duplicate
- Remove state parameter from BotAI.on_step


---
*Generated 2026-04-02 from git commit history and PyPI release metadata.*
---

## ═══════════════════════════════════════════════════════
##  🔀  FORK POINT  —  burnysc2 forked from sc2 @ 0.11.2
## ═══════════════════════════════════════════════════════

The releases below belong to the **original `sc2` package** (Dentosal/python-sc2).
From 0.11.2 onward, development continued separately in the burnysc2 fork.
See `CHANGELOG.md` for the burnysc2-specific history above this line.

---

# Changelog  (original sc2 package — Dentosal/python-sc2)

All notable changes to this project are documented in this file.
This file covers the **original `sc2` package** (PyPI) from which
`burnysc2` was forked. The burnysc2 fork has its own CHANGELOG.md.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.11.x Series  —  2019-02-07 → 2019-12-01
*Releases in this series: 3*

### [0.11.2] - 2019-12-01
#### Added
- Add fix for SC2 Client 4.9.0 to 4.9.3
- Update expansionlocations again, add dump data, unit.can_be_attacked
- Fix pickle generator, add missing pickle file 16bit
- Fix tests for new ramps and vision blocker function
- Add resource ratio and fix crash on no minerals on map
- Add terran to z height function, fix typo, fix test
- Add note to is_visible, is_revealed, attack/armor/shield upgrades, buff time to unit. Add alert check, use try/except in prevent double actions
- Add is_transforming and can_attack_both
- Add add self.response_observation for tests
- Add devtools, add watchtowers, speed up unit loop in game state
- Add rounded for point2 and 3, remove from pointlike
- Fix pixelmaps, ramp walls, and tests. Update pickle files with new proto data
- Start fixing bugs with new client update
- Add comments
- Add tweakimp's expansion locations fix
- Add assert string message
- Add more tests that use pickle files
- Fix TypeError log on game end, add try execpt blocks to cut isinstance calls, change point equality to be exact
- Add example usages
- Add assert to test to understand failure
- Speed up can_place and already_pending_upgrade, add EffectData __repr__ , add Point2 __hash__, improve Pointlike __eq__, improve unit __hash__ and __eq__
- Add Unit.is_using_ability
- Add is_further_than
- Add deprecation note for gamedata change
- Add autocast toggle function
- Add debug text example
- Add option for fullscreen windows
- Add Pointlike.is_closer_than(dist, pos)
- Add AIBuilds
- Merge from master, fix take, add cargo_left
#### Fixed
- Fix tests
- Fix ramp finding code, improve tests, compress pickle files with lzma
- Change walls for impossible ramps (HonorgroundsLE) so that they return None or empty set instead of crashing the game
- Reduce minimum amount of expansions to 10 (fix for bel'shir vestige)
- Fix .travis.yml
- Remove old_distance_to from test, fix blipunits in gamestate
- fix last typos
- Fix wrong variables and comparison in distribute workers
- Fix closest and furthest in botai and self.unit in game state
- Prevent key error in _find_groups
- Fix distribute workers, only get units objects in game state if we need them
- Fix proper termination on game end, fix on_end trigger on ladder server
- Fix game state alliance bug
- Fix line in .travis.yml
- Fix expansion locations height errors
- Fix pointlike __eq__
- Fixes bad import in renderer.py
- Also show position in debug example
- Fix typos
- Fix some types, clean game step
- Fix ability crash
- Try to fix enemy race crash, improve cache
- Workaround for zerg supply rounding bug
- Fix map area, Fix pixelmap getter and setter
- Make _find_groups a generator,format imports,fix crash in can_cast
- Fix property_cache_once_per_frame
- Use more _distance_squared, fix empty units call crash
- Fix bot_ai.py
- Fix units.py
- Fix bug in expand_now when location=None
- Fix main.py
- Fix crash when a realtime game ends
- Fix dead units, get complete game data
- Fix crash on game over race condition
#### Changed
- Update pickle files to make tests pass
- Update client.py
- Unignore compressed pickle test files
- Organize .gitignore
- Ignore pickle data
- Speed up expansion locations
- Update bot_ai.py
- Use isdisjoint in buff checks, find vision blockers in game info
- Increase resource threshold for automaton middle bases
- Dont use huge numbers in tests, set epsilon for distance tests
- Speed up resource buffs and unit creation in game state
- Use math.hypot for distance calculation
- Update distribute_workers
- Dont run autotestbot
- Roll back to epsilon difference on position __eq__
- Update expansion locations
- Change directory name
- Update tests with Unit and Units, change cache so it is bot-based not function-based
- Change logger to info
- Apply Black
- Update pipfile
- Shortcut is_using_ability if no orders
- Numpy entered the room.
- Use is_using_ability for more things
- Allow passing a set of abilities to is_using_ability
- Update autotest_bot.py
- Revert autotest formatting
- Improve double actions
- Prevent double actions
- Update warning and ids
- Update ids
- Improve upper and lower ramp loops
- Roll back property_cache_once_per_frame
- Update ids and their generator
- improve select_build_worker
- Workaround for incorrectly set lurker morph ability
- Format zerg supply correction
- Improve actions and bot_ai
- Speed up client, bot_ai and game_state
- Clarify deprecation notice
- Don't include enemy_race when running on a single player map
- Filter out unavailable abilities
- Update Dockerfile using SC2 client version 4.7.1
- return the line of the occurrence and simplify it a bit
- Addition for Cost objects
- deprecate warning for duplicated functions
- Trailing whitespace
- Use generators and dont use game_data where we dont need it
- Use do_actions() instead of do() in WorkerRushBot
- Update unit.py
- Rewrite unit.py, clean unitcommand
- comment out test 5
- Test if test completes without chat
- Improve upper and lower in Ramp
- Ignore closed connections in response to quit requests
- Use comprehension, squared distance, faster ramps
#### Removed
- Remove junk file
- Remove unnecessary import
- Remove unnecessary assert
- Remove test file
- remove alert tests
- Update pathinggrid every frame, use try except in unit._weapons, remove unnecessary isinstance calls
- Remove comments
- Remove test_positions from autotest_bot
- Remove offset overwrite
- Update ids, remove unneccessary property caches

### [0.11.1] - 2019-02-11
#### Added
- Merge from master, add asserts
- Add idle worker count, army_count, warp_gate_count, larva_count to botai
- Add zergling for exception
- Add assert strings
#### Fixed
- Fix difficulty
#### Changed
- Allow setting player names

### [0.11.0] - 2019-02-07
#### Added
- Add is_detector property
#### Fixed
- Fix issue when timeout during ws send causes out-of-sync messaging
- Fix missing cache, improve some assert statements
#### Changed
- Update gitignore
- Log player scores
- Remerge Burnys commits

## 0.10.x Series  —  2018-10-13 → 2019-02-04
*Releases in this series: 12*

### [0.10.11] - 2019-02-04
#### Added
- Add alerts, and worker/army supply
- Fix ramp bug on map Acolyte and add cache for ramp points
- Remove .rounded in self.build function, Add quick_save and quick_load client.py functions
- Add on_upgrade_complete event
- Add on_start_async method (changing on_start to async may confuse many authors) and reorganize main.py structure Now at on_start and on_start_async, game_data and game_info and game_state (self.state) information will be available
- Add debug (cheat) function
- Add more verbose log output
#### Fixed
- FIx Human string issue
- fixC
- fixB
- Fix debug_text_simple
- Improve asserts and fix Units.take function
- Fix missing var
#### Changed
- rollback1
- Merge master into develop
- Merge from master
- Set default of already_pending to all_units=True to always include morphing units (e.g. morphing from hatch to lair)
- Stop counting terran structures twice in already_pending function
- Update comments and allow Unit and Units to be allowed for several commands
- Clear sliding window on timeout penalty
- Inform bot about it's time budget with it's limited
- Adds 'on_building_construction_started' event hook to the bot.
#### Removed
- Remove bool type check

### [0.10.10] - 2019-01-15
*No tracked commits in this release window.*

### [0.10.9] - 2019-01-15
#### Added
- Add more caching and update comments
- Add more time limit options
- Add bonus damage
- unit overhaul, inherit from passengerunit and add comments
- Add ressources selection
#### Fixed
- Fix weapons in unit, improve game state init, cache typeid
- Fix unit object class name
- Fix import crash
- Fix crash
#### Changed
- Update game_info
- Update IDs
- Update pixel_map.py
- Clean units.py
- Update units.py
- Update cache.py
- Update client.py
- Clean up update
- Clean up with Burny
- Do not use same unit multiple times in one action
#### Removed
- Remove top secret variable

### [0.10.8] - 2019-01-09
#### Changed
- Update client.py
- Update PixelMap

### [0.10.7] - 2019-01-06
#### Added
- add UnitTypeId import
- Use ressource ids, add TODO
- Add random_seed parameter
- Add WineLinux platform and SC2PF envvar to set the platform
- Add can_attack property (#185)
- Add GameData parsing optimization
#### Fixed
- Fix list initialization
- Fix parenhesis, comment out error handling
- Fix indent
- Tweakimp patch (#186)
- Fix move_camera (#184)
- Update unit_typeid to fix Viking enum
- Fixed a typo
- Fix Para Site ramp crash
- Hackfix: Improve ramp code speed
- Don't crash on expand_now when no townhalls are left
- Fix a bug that prevents making overlord on negative supply
#### Changed
- Update more
- Update position.py
- Update game_state.py
- Improve expansion location even further
- current status
- Stop expand if no more places for expanding
- Update README.md (#182)
- Update pixel_map.py
- Update unit.py
- Update bot_ai.py
- Only check structures for building completion
- update ramp_wall.py example
- update proxy_rax.py example
- update onebase_battlecruiser.py example
- update cyclone_push.py example
- update warpgate_push.py example
- update threebase_voidray.py example
- update cannon_rush.py example
- update worker_rush.py example
- update distributed_workers.py example
- update zerg_rush.py example
- update hydralisk_push.py example
- update onebase_broodlord.py example
- Update unit.py (#172)
- update
- Improve expansion location (#167)
- Relocate the game_info.find_ramps() call
- Import bisect
- Find point clusters during ramp search faster
- Load abilities faster
#### Removed
- Delete settings.json

### [0.10.6] - 2018-10-14
#### Fixed
- Fix issues with distribute_workers
#### Changed
- Build a list of actions in distribute_workers
- Do not exit when action cannot be afforded, just log a warning

### [0.10.5] - 2018-10-13
*No tracked commits in this release window.*

### [0.10.4] - 2018-10-13
*No tracked commits in this release window.*

### [0.10.3] - 2018-10-13
*No tracked commits in this release window.*

### [0.10.2] - 2018-10-13
*No tracked commits in this release window.*

### [0.10.1] - 2018-10-13
*No tracked commits in this release window.*

### [0.10.0] - 2018-10-13
#### Added
- Add a working RGB renderer on Linux
- Add resource height comparison for resource groups
- Add same tech and same unit filter
- Add minor performance improvements
- Add mypy type checking
- Add Point2 vector functions and operators
- Improve distance calculation and add sorted_by_distance_to
- Add repair and is_repairing
- Fix Techlab and Reactor cost, add mypy type checking
- Add Blizzard's EULA agreement
- Add is_construction_scv property
- Add arcade map bot example
- Add simple PixelMap info getters
- Add returning and collecting properties / filters
- Add missing await statement on issue_events
- Add surrender hint
- Add target_in_range test
- Add furthest_distance_to
- Add target type enum
- Add tests for position.py, unit.py and units.py
- Add method on_end
- Add can_feed to can_afford check
- Add debug_unit_function
- Add "not"
- Add the last missing data to score.py
- Add opponent_id to bot class for sc2ai ladder
- Add PassengerUnit to support cargo units
- Add "is_psionic" property (#111)
#### Fixed
- Fix resource spread threshold and some calculation speedup
- Fix minor issues
- Fix center function for type checking
- Fix Point2 vector functions and operators
- Fix indention
- Fix __repr__()
- Fix is_visible()
- Fix another typo
- Fix typo
- Fix expansion position in threebase_voidray example.
- Fix ramp bug on ParaSite SC2 map
- Fix missing upgrade by adding an index to enum name
- Fix expand_now()
- Fix testbot file name
#### Changed
- ExecuteInfo.txt parsing
- Improve expansion_location
- Revert some changes
- Change list to set
- Change if else to dict
- Make events async
- Include unit radius in target_in_range function
- Update to version 0.9.0
#### Removed
- Remove isinstance(p, Unit) call
- Remove assert in prepare_first_step()
- Remove cargo_size duplicate

## 0.9.x Series  —  2018-08-06 → 2018-08-06
*Releases in this series: 1*

### [0.9.0] - 2018-08-06
#### Added
- Add important test for do_actions() (#102)
- Add headless linux tests to travis CI testing (#101)
- Add already_pending for upgrades
- Add comments and mypy type checking (#95)
- Add enemy_race and time property to bot_ai.py, improve comments in client.py
- Add score, mypy type checking and more (#89)
- Add missing properties of ResponseObservarion to game_state.py
- Add gitignore PyCharm project folder
- Add on_unit_created and on_unit_destroyed and on_building_construction_complete
- Add ignore_resource_requirements parameter to be used in available abilities query
- Add different functions to print debug text
- Add travis CI unittests (#88)
- Add closest_distance_to and a few asserts
- Add a bot example that uses the newly implemented attributes and functions
- Add debug spawn unit function
- Add check if unit can cast an ability - energy cost and ability range
- Add dead unit events, effects and upgrades
- Fix crash when enemy in sensor tower range + support destructible rocksu
- Add furthest_to filter mainly for units stutter stepping backwards
- Add Units.further_than filter
- Add resource subtraction on action execute attempt
- Add function for multiple actions at once (but without can_afford)
- Add weapon_cooldown to Unit attributes
- Add furthest away method
- Add gathering and center of units
- Add checks if Unit can attack ground and/or air
- Implement fast reloading (fixes #40)
- Add Units filters that use the new Unit attributes
- Add missing ability (212) to ability_id
#### Fixed
- Make to_debug_color accept lists and tuples as arguments
- Fix mypy type check
- Fix cost of zerg structures and building morph cost (#98)
- Fix debug_create_unit
- Hotfix query_available_abilities (#94)
- Fix main ramp walling (#92)
- Fix typo in "AbilityId" name
- Fix issues created by merges
- Fix indent
- Fix formatting
- Fix error occurred after removing resonseObservation from GameState
- Fix misplaced bracket
- Fixes and improvements
- Fix missing self
- Fix e2e slow test suite
- Fix typo in control_group.py
- Fix center property
- Fix to surplus_havesters, added more unit info
- Fix a bug for pixel map on non-square maps
- Fix and polish to effect data
- Fix to pixel map (y position was reversed) Added visibility and creep to self.state
- Fix "center of units"
- Tweak the error message
- Fix moving/attacking/gathering
- Fixed typo in control_group.py
#### Changed
- Break some ramp code
- Update Pipfile
- Update README
- Upgrade to Python 3.7 and Pipenv
- Manually change effects because effect_id.py doesnt seem to be complete
- Do a minor change to Unit.order_target
- Added a few more attributes
- Use 2d positions by default
- Clean up stable id generate script
#### Removed
- Remove accidental "not" in the units.gathering property

## 0.8.x Series  —  2018-06-07 → 2018-06-18
*Releases in this series: 5*

### [0.8.4] - 2018-06-18
*No tracked commits in this release window.*

### [0.8.3] - 2018-06-18
*No tracked commits in this release window.*

### [0.8.2] - 2018-06-18
#### Added
- Add warning about BotAI.distribute_workers slowness
#### Fixed
- Fix a crash when game ends one step before the results are available
- Fix some names and paths in examples
#### Changed
- Speed up warpgate example a bit

### [0.8.1] - 2018-06-13
#### Added
- Add more examples
#### Changed
- Update readme

### [0.8.0] - 2018-06-07
#### Added
- Add simplified debug_text to client.py
- Add Broodlord example for zerg
#### Fixed
- Fix command to start cannon_rush example
- Properly warn about incorrect map path, fixes #12
#### Changed
- Change query_available_abilities to allow multiple per call requests
- Also look for map files in the Map root directory.
- Organize examples directories
- WIP

## 0.7.x Series  —  2018-02-22 → 2018-05-11
*Releases in this series: 10*

### [0.7.9] - 2018-05-11
#### Added
- Also enable verbose logging for sc2 process
#### Changed
- Update README.md with info on getting started (#35)

### [0.7.8] - 2018-02-26
#### Added
- Add ramp support
- WIP ramp support
- Add initial ramp map
#### Fixed
- Fix couple of calls to Pointlike.distance
- Fix expansion location discovery
#### Changed
- WIP ramp wall bot
- Revert some breaking changes
- Cleanup
- Tweak EXPANSION_GAP_THRESHOLD

### [0.7.7] - 2018-02-23
*No tracked commits in this release window.*

### [0.7.6] - 2018-02-23
*No tracked commits in this release window.*

### [0.7.5] - 2018-02-23
*No tracked commits in this release window.*

### [0.7.4] - 2018-02-23
#### Added
- Add modification operations to control groups
- Add control group helper
- Add some unit tests for directions
#### Fixed
- Fix gametime limit for computer vs human games
- Rename and fix towards_with_random_angle
#### Changed
- Improve BotAI.already_pending
- Update .gitignore
- Cleanup

### [0.7.3] - 2018-02-22
*No tracked commits in this release window.*

### [0.7.2] - 2018-02-22
*No tracked commits in this release window.*

### [0.7.1] - 2018-02-22
*No tracked commits in this release window.*

### [0.7.0] - 2018-02-22
#### Fixed
- Fix resigning on bot crash
- Catch and log errors in BotAI.on_step

## 0.6.x Series  —  2018-02-01 → 2018-02-16
*Releases in this series: 6*

### [0.6.5] - 2018-02-16
*No tracked commits in this release window.*

### [0.6.4] - 2018-02-16
#### Added
- Add an option to limit game max length
- Add game_loop to state to indicate elapsed game time
#### Fixed
- Fix voidray example

### [0.6.3] - 2018-02-15
*No tracked commits in this release window.*

### [0.6.2] - 2018-02-15
#### Fixed
- Fix command center selection in example
#### Changed
- Added a note about sc2-bot-match-runner repository

### [0.6.1] - 2018-02-13
#### Added
- Warpgate support  (#28)
#### Fixed
- Fix indent
#### Changed
- Clarification for map locations
- Use `stableid.json` to generate ID enums (#24)
- `Unit.has_buff` and `BotAI.get_available_abilities(unit)` (#25)
- `BotAI.already_pending` enhancement (#21)
- `BotAI.distribute_workers` convenience method (#20)
- Log player id before game starts

### [0.6.0] - 2018-02-01
#### Added
- Add new terran example
#### Fixed
- Fix missing self
- Fix realtime argument
#### Changed
- `BotAI.can_afford` result wrapper (#23)
#### Removed
- Remove state parameter from BotAI.on_step

## 0.5.x Series  —  2018-01-30 → 2018-01-30
*Releases in this series: 1*

### [0.5.0] - 2018-01-30
#### Added
- Add a convenience method to expand to the nearest unoccupied expansion
#### Fixed
- Fixes #13
- Fix the case when Paths.CWD is None
#### Changed
- Rename expand_to_nearest to expand_now for conciseness
- Do expansion occupation checking first before querying pathing
- Directly return value instead of assigning to an unused variable
- Tweak `next_expansion` identification to ignore locations with nearby town halls
- Allow more fine-grained control on how building placement should be done

## 0.4.x Series  —  2018-01-18 → 2018-01-26
*Releases in this series: 7*

### [0.4.6] - 2018-01-26
#### Added
- Add logging for replay save operation
#### Fixed
- Replace base_dir to self.BASE to fix unresolved variable
#### Changed
- Invoke str() on paths during _launch()
- Allow using save_replay_as in _join_game when called directly
- Lazily loads paths to allow importing the library even if SC2 isn't installed

### [0.4.5] - 2018-01-23
*No tracked commits in this release window.*

### [0.4.4] - 2018-01-23
#### Added
- Add possibility to detect add ons
#### Fixed
- Fix executable paths on Linux
#### Changed
- Use relative path for maps
- Update data ids

### [0.4.3] - 2018-01-19
#### Added
- Add a slow bot to test timeout feature
#### Changed
- Improve logging and handling of closed connections
- Improve proxy rax example
- Allow setting per-step timeout for BotAI
- Set up logger

### [0.4.2] - 2018-01-18
*No tracked commits in this release window.*

### [0.4.1] - 2018-01-18
*No tracked commits in this release window.*

### [0.4.0] - 2018-01-18
*No tracked commits in this release window.*

## 0.3.x Series  —  2017-12-18 → 2018-02-13
*Releases in this series: 3*

### [0.3.2] - 2018-02-13
#### Added
- Warpgate support  (#28)
- Add new terran example
- Add a convenience method to expand to the nearest unoccupied expansion
- Add logging for replay save operation
- Add possibility to detect add ons
- Add a slow bot to test timeout feature
- Add JSON serialization support for portconfig
- Add three base void ray strategy example
- Add methods for expanding to new bases
- Add some new fields to the unit (from the last API update)
- Add wiki link to the readme
- Add support for sending chat messages
- Add bot vs bot example
#### Fixed
- Fix indent
- Fix missing self
- Fix realtime argument
- Fixes #13
- Fix the case when Paths.CWD is None
- Replace base_dir to self.BASE to fix unresolved variable
- Fix executable paths on Linux
- Fix unawaited call in the cannon rush example
- Fix small consistency issues
- Typofix
- Eliminate the "game already ended" error
- Fix exit-crash bugs
- Fix subpackage imports
#### Changed
- Clarification for map locations
- Use `stableid.json` to generate ID enums (#24)
- `Unit.has_buff` and `BotAI.get_available_abilities(unit)` (#25)
- `BotAI.already_pending` enhancement (#21)
- `BotAI.distribute_workers` convenience method (#20)
- Log player id before game starts
- `BotAI.can_afford` result wrapper (#23)
- Rename expand_to_nearest to expand_now for conciseness
- Do expansion occupation checking first before querying pathing
- Directly return value instead of assigning to an unused variable
- Tweak `next_expansion` identification to ignore locations with nearby town halls
- Allow more fine-grained control on how building placement should be done
- Invoke str() on paths during _launch()
- Allow using save_replay_as in _join_game when called directly
- Lazily loads paths to allow importing the library even if SC2 isn't installed
- Use relative path for maps
- Update data ids
- Improve logging and handling of closed connections
- Improve proxy rax example
- Allow setting per-step timeout for BotAI
- Set up logger
- Allow running clients on different processes
- Allow bots without AI object for external games
- Play against Terran instead of Zerg in examples
- Allow custom hostname and port for sc2process websocket
- Update README.md
- Use generic names in the worker rush example
- Allow saving replays
- Ignore .cache folder
- Improve resource cost calculations
#### Removed
- Remove state parameter from BotAI.on_step

### [0.3.1] - 2017-12-18
*No tracked commits in this release window.*

### [0.3.0] - 2017-12-18
#### Added
- Add automatic tests
- Add leave command to cleanly exit games
- Add TvZ Human vs AI example
- Add portconfig class
- Add repr method for cost
- Add possibility to run multiple clients
#### Fixed
- Fix cannon rush bot
- Clean up error handling and reporting
- Fix singleplayer
- Remove redundant debug prints
#### Changed
- Update examples to match library changes
- Update to match latest API changes
- Clean up ZergRushBot example

## 0.2.x Series  —  2017-08-30 → 2017-08-31
*Releases in this series: 2*

### [0.2.1] - 2017-08-31
#### Added
- Add proxy rax example for terran
- Add id autogeneration script and result files
#### Changed
- Clean up unused imports in examples
- Make examples importable
- Polish README.md
- Rewrite selection system to use constants instead of strings

### [0.2.0] - 2017-08-30
#### Added
- Add debug text drawing
- Add zerg(ling) rush example
- Add signal handler to always clean up after the game ends
- Add group operations
- Add non-exact name comparison
- Add new example: cannon rush
- Update examples to match the new syntax
- Add unit commands and selectors
#### Fixed
- Fix an issue when joining as observer
#### Changed
- Properly quit from the game
- Impl repr
- Prepare with vespenen gas count too
- Allow targeting both units and positions
- Update readme
#### Removed
- Remove dependency "vectors"

## 0.1.x Series  —  2017-08-16 → 2017-08-19
*Releases in this series: 2*

### [0.1.1a0] - 2017-08-19
#### Added
- Add mention about releases and tags
- Rename to "sc2", add setup.py
- Add worker rush and required code
#### Changed
- Clean up action commands
- Allow returning None from on_step method
- Update description
- Clean up paths module
- Require Python 3.6+
- Use github releases
- Prepare for pypi release
- Update README.md

### [0.1.0a1] - 2017-08-16
#### Changed
- Separate player logic from communication logic
- Initial, niminal useful version
- Initial commit
