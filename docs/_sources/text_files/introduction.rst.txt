*************
Introduction
*************

Requirements
-------------
- Python 3.7 or newer
- StarCraft 2 Client installation in the **default installation path** which should be ``C:\Program Files (x86)\StarCraft II``

Installation
-------------
Install through pip using ``pip install burnysc2`` if Python is in your environment path, or go into your python installation folder and run through console ``python -m pip install burnysc2``.

Alternatively (of if the command above doesn't work) you can install a specific branch directly from github, here the develop branch::

    pip install pipenv
    pip install --upgrade --force-reinstall https://github.com/BurnySc2/python-sc2/archive/develop.zip

Creating a bot
---------------
A basic bot can be made by creating a new file `my_bot.py` and filling it with the following contents::

    import sc2
    from sc2.bot_ai import BotAI
    class MyBot(BotAI):
        async def on_step(self, iteration: int):
            print(f"This is my bot in iteration {iteration}!"

    sc2.run_game(
        sc2.maps.get(map), [Bot(Race.Zerg, MyBot()), Computer(Race.Zerg, Difficulty.Hard)], realtime=False
    )

You can now run the file using command ``python my_bot.py`` or double clicking the file.

A SC2 window should open and your bot should print the text several times per second to the console. Your bot will not do anything else because no orders are issued to your units.

Available information in the game
------------------------------------

Information about your bot::

    # Resources and supply
    self.minerals: int
    self.vespene: int
    self.supply_army: int # 0 at game start
    self.supply_workers: int # 12 at game start
    self.supply_cap: int # 14 for zerg, 15 for T and P at game start
    self.supply_used: int # 12 at game start
    self.supply_left: int # 2 for zerg, 3 for T and P at game start

    # Units
    self.larva_count: int # 3 at game start (only zerg)
    self.warp_gate_count: Units # Your warp gate count (only protoss)
    self.idle_worker_count: int # Workers that are doing nothing
    self.army_count: int # Amount of army units
    self.workers: Units # Your workers
    self.larva: Units # Your larva (only zerg)
    self.townhalls: Units # Your townhalls (nexus, hatchery, lair, hive, command center, orbital command, planetary fortress
    self.gas_buildings: Units # Your gas structures (refinery, extractor, assimilator
    self.units: Units # Your units (includes larva and workers)
    self.structures: Units # Your structures (includes townhalls and gas buildings)

    # Other information about your bot
    self.race: Race # The race your bot plays. If you chose random, your bot gets assigned a race and the assigned race will be in here (not random)
    self.player_id: int # Your bot id (can be 1 or 2 in a 2 player game)
    # Your spawn location (your first townhall location)
    self.start_location: Point2
    # Location of your main base ramp, and has some information on how to wall the main base as terran bot (see GameInfo)
    self.main_base_ramp: Ramp

Information about the enemy player::

    # The following contains enemy units and structures inside your units' vision range (including invisible units, but not burrowed units)
    self.enemy_units: Units
    self.enemy_structures: Units

    # Enemy spawn locations as a list of Point2 points
    self.enemy_start_location: List[Point2]

    # Enemy units that are inside your sensor tower range
    self.blips: Set[Blip]

    # The enemy race. If the enemy chose random, this will stay at random forever
    self.enemy_race: Race

Other information::

    # Neutral units and structures
    self.mineral_field: Units # All mineral fields on the map
    self.vespene_geyser: Units # All vespene fields, even those that have a gas building on them
    self.resources: Units # Both of the above combined
    self.destructables: Units # All destructable rocks (except the platforms below the main base ramp)
    self.watchtowers: Units # All watch towers on the map (some maps don't have watch towers)
    self.all_units: Units # All units combined: yours, enemy's and neutral

    # Locations of possible expansions
    self.expansion_locations: Dict[Point2, Units]

    # Game data about units, abilities and upgrades (see game_data.py)
    self.game_data: GameData

    # Information about the map: pathing grid, building placement, terrain height, vision and creep are found here (see game_info.py)
    self.game_info: GameInfo

    # Other information that gets updated every step (see game_state.py)
    self.state: GameState

    # Extra information
    self.realtime: bool # Displays if the game was started in realtime or not. In realtime, your bot only has limited time to execute on_step()
    self.time: float # The current game time in seconds
    self.time_formatted: str # The current game time properly formatted in 'min:sec'

Possible bot actions
---------------------

The game has started and now you want to build stuff with your mined resources. I assume you played at least one game of SC2 and know the basics, for example where you build drones (from larva) and SCVs and probes (from command center and nexus respectively).

Training a unit
^^^^^^^^^^^^^^^^

Assuming you picked zerg for your bot and want to build a drone. Your larva is available in ``self.larva``. Your bot starts with 3 larva. To choose which of the larva you want to issue the command to train a drone, you need to pick one. The simplest you can do is ``my_larva = self.larva.random``. Now you have to issue a command to the larva: morph to drone.

You can issue commands using the function ``self.do(action)``. You have to import ability ids before you can use them. ``from sc2.ids.ability_id import AbilityId``. Here, the action can be ``my_action = my_larva(AbilityId.LARVATRAIN_DRONE)``. In total, this results in::

    from sc2.ids.ability_id import AbilityId

    my_larva = self.larva.random
    my_action = my_larva(AbilityId.LARVATRAIN_DRONE)
    self.do(action)
    # Or the old way to do this was
    # self.action.append(my_action)

Important: The action will be issued after the ``on_step`` function is completed and the bot communicated with the SC2 Client over the API. This can result in unexpected behavior. Your larva count is still at three (``self.larva.amount == 3``), your minerals are still at 50 (``self.minerals == 50``) and your supply did not go up (``self.supply_used == 12``), but expected behavior might be that the larva amount drops to 2, self.minerals should be 0 and self.supply_used should be 13 since the pending drone uses up supply.

The last two issues can be fixed by calling the ``self.do`` function differently, specifically::

    self.do(self.larva.random(AbilityId.LARVATRAIN_DRONE), subtract_cost=True, subtract_supply=True)

The keyword arguments are optional because many actions are move or attack commands, instead of train or build commands, thus making the bot slightly faster if only specific actions are checked if they have a cost associated.

There are two more ways to do the same::

    from sc2.ids.unit_typeid import UnitTypeId

    self.do(self.larva.random.train(UnitTypeId.DRONE), subtract_cost=True, subtract_supply=True)

This converts the UnitTypeId to the AbilityId that is required to train the unit.

Another way is to use the train function from the api::

    self.train(UnitTypeId.DRONE, amount=1)

This tries to figure out where to build the target unit from, and automatically subtracts the cost and supply after the train command was issued. If performance is important to you, you should try to give structures the train command directly from which you know they are idle and that you have enough resources to afford it.

So a more performant way to train as many drones as possible is::

    for loop_larva in self.larva:
        if self.can_afford(UnitTypeId.DRONE):
            self.do(loop_larva.train(UnitTypeId.DRONE), subtract_cost=True, subtract_supply=True)
            # Add break statement here if you only want to train one
        else:
            # Can't afford drones anymore
            break

``self.can_afford`` checks if you have enough resources and enough free supply to train the unit. ``self.do`` then automatically increases supply count and subtracts resource cost.

Warning: You need to prevent issuing multiple commands to the same larva in the same frame (or iteration). The ``self.do`` function automatically adds the unit's tag to ``self.unit_tags_received_action``. This is a set with integers and it will be emptied every frame. So the final proper way to do it is::

    for loop_larva in self.larva:
        if loop_larva.tag in self.unit_tags_received_action:
            continue
        if self.can_afford(UnitTypeId.DRONE):
            self.do(loop_larva.train(UnitTypeId.DRONE), subtract_cost=True, subtract_supply=True)
            # Add break statement here if you only want to train one
        else:
            # Can't afford drones anymore
            break

Building a structure
^^^^^^^^^^^^^^^^^^^^^

Nearly the same procedure is when you want to build a structure. All that is needed is

- Which building type should be built
- Can you afford building it
- Which worker should be used
- Where should the building be placed

The building type could be ``UnitTypeId.SPAWNINGPOOL``. To check if you can afford it you do ``if self.can_afford(UnitTypeId.SPAWNINGPOOL):``.

Figuring out which worker to use is a bit more difficult. It could be a random worker (``my_worker = self.workers.random``) or a worker closest to the target building placement position (``my_worker = self.workers.closest_to(placement_position)``), but both of these have the issue that they could use a worker that is already busy (scouting, already on the way to build something, defending the base from worker rush). Usually worker that are mining or idle could be chosen to build something (``my_worker = self.workers.filter(lambda worker: worker.is_collecting or worker.is_idle).random``). There is an issue here that if the Units object is empty after filtering, ``.random`` will result in an assertion error.

Lastly, figuring out where to place the spawning pool. This can be as easy as::

    map_center = self.game_info.map_center
    placement_position = self.start_location.towards(map_center, distance=5)

But then the question is, can you actually place it there? Is there creep, is it not blocked by a structure or enemy units? Building placement can be very difficult, if you don't want to place your buildings in your mineral line or want to leave enough space so that addons fit on the right of the structure (terran problems), or that you always leave 2x2 space between your structures so that your archons won't get stuck (protoss and terran problems).

A function that can test which position is valid for a spawning pool is ``self.find_placement``, which finds a position near the given position. This function can be slow::

    map_center = self.game_info.map_center
    position_towards_map_center = self.start_location.towards(map_center, distance=5)
    placement_position = await self.find_placement(UnitTypeId.SPAWNINGPOOL, near=position_towards_map_center, placement_step=1)
    # Can return None if no position was found
    if placement_position:

One thing that was not mentioned yet is that you don't want to build more than 1 spawning pool. To prevent this, you can check that the number of pending and completed structures is zero::

    if self.already_pending(UnitTypeId.SPAWNINGPOOL) + self.structures.filter(lambda structure: structure.type_id == UnitTypeId.SPAWNINGPOOL and structure.is_ready).amount == 0:
        # Build spawning pool

So in total: To build a spawning pool in direction of the map center, it is recommended to use::

    if self.can_afford(UnitTypeId.SPAWNINGPOOL) and self.already_pending(UnitTypeId.SPAWNINGPOOL) + self.structures.filter(lambda structure: structure.type_id == UnitTypeId.SPAWNINGPOOL and structure.is_ready).amount == 0:
        worker_candidates = self.workers.filter(lambda worker: (worker.is_collecting or worker.is_idle) and worker.tag not in self.unit_tags_received_action)
        # Worker_candidates can be empty
        if worker_candidates:
            map_center = self.game_info.map_center
            position_towards_map_center = self.start_location.towards(map_center, distance=5)
            placement_position = await self.find_placement(UnitTypeId.SPAWNINGPOOL, near=position_towards_map_center, placement_step=1)
            # Placement_position can be None
            if placement_position:
                build_worker = worker_candidates.closest_to(placement_position)
                self.do(build_worker.build(UnitTypeId.SPAWNINGPOOL, placement_position, subtract_cost=True)

The same can be achieved with the convenience function ``self.build`` which automatically picks a worker and internally uses ``self.find_placement``::

    if self.can_afford(UnitTypeId.SPAWNINGPOOL) and self.already_pending(UnitTypeId.SPAWNINGPOOL) + self.structures.filter(lambda structure: structure.type_id == UnitTypeId.SPAWNINGPOOL and structure.is_ready).amount == 0:
        map_center = self.game_info.map_center
        position_towards_map_center = self.start_location.towards(map_center, distance=5)
        await self.build(UnitTypeId.SPAWNINGPOOL, near=position_towards_map_center, placement_step=1)













