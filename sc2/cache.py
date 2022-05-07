from __future__ import annotations

from typing import TYPE_CHECKING, Callable, TypeVar

if TYPE_CHECKING:
    from sc2.bot_ai import BotAI

T = TypeVar("T")


class property_cache_once_per_frame(property):
    """This decorator caches the return value for one game loop,
    then clears it if it is accessed in a different game loop.
    Only works on properties of the bot object, because it requires
    access to self.state.game_loop

    This decorator compared to the above runs a little faster, however you should only use this decorator if you are sure that you do not modify the mutable once it is calculated and cached.

    Copied and modified from https://tedboy.github.io/flask/_modules/werkzeug/utils.html#cached_property
    # """

    def __init__(self, func: Callable[[BotAI], T], name=None):
        # pylint: disable=W0231
        self.__name__ = name or func.__name__
        self.__frame__ = f"__frame__{self.__name__}"
        self.func = func

    def __set__(self, obj: BotAI, value: T):
        obj.cache[self.__name__] = value
        obj.cache[self.__frame__] = obj.state.game_loop

    def __get__(self, obj: BotAI, _type=None) -> T:
        value = obj.cache.get(self.__name__, None)
        bot_frame = obj.state.game_loop
        if value is None or obj.cache[self.__frame__] < bot_frame:
            value = self.func(obj)
            obj.cache[self.__name__] = value
            obj.cache[self.__frame__] = bot_frame
        return value
