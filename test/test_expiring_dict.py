import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sc2.expiring_dict import ExpiringDict

def test_class():
    class State:
        def __init__(self):
            self.game_loop = 0

    class BotAI:
        def __init__(self):
            self.state = State()

        def increment(self, value=1):
            self.state.game_loop += value

    test_dict = {"hello": "its me mario", "does_this_work": "yes it works", "another_test": "yep this one also worked"}

    bot = BotAI()
    test = ExpiringDict(bot, max_len=3, max_age_frames=10)

    for key, value in test_dict.items():
        test[key] = value
    bot.increment()

    # Test len
    assert len(test) == 3

    # Test contains method
    assert "hello" in test
    assert "doesnt_exist" not in test

    # Get item
    result = test["hello"]
    assert result == "its me mario"

    # Get item that doesnt exist
    try:
        result = test["doesnt_exist"]
    except KeyError:
        pass
    assert result == test["hello"]

    # Test maxlen == 3
    assert len(test) == 3

    # Set item, this kicks the first item with key "hello"
    test["setitem"] = "test"

    assert len(test) == 3

    # Test iteration
    for key, item in test.items():
        assert key in test
        assert test[key] == item, (key, item)
        assert test.get(key) == item
        assert test.get(key, with_age=True)[0] == item
        assert test.get(key, with_age=True)[1] in {0, 1}

    for key in test.keys():
        pass

    for value in test.values():
        pass

    # Update from another dict
    updater_dict = {"new_key": "my_new_value"}
    test.update(updater_dict)
    assert "does_this_work" not in test
    assert "new_key" in test

    # Test pop method
    new_key = test.pop("new_key")
    assert new_key == "my_new_value"

    # Show the expiring dict
    # print(test)
    assert repr(test) == "ExpiringDict('another_test': ('yep this one also worked', 0), 'setitem': ('test', 1))"
    assert str(test) == "ExpiringDict('another_test': ('yep this one also worked', 0), 'setitem': ('test', 1))"

    # Advance the frames by 10, this means all entries should now be invalid
    bot.increment(10)

    for key in test.keys():
        assert False

    for value in test.values():
        assert False

    for key, value in test.items():
        assert False

    assert "new_key" not in test
    assert "setitem" not in test
    # len doesn't work at the moment how it should - all items in the dict are expired, so len should return 0
    # assert len(test) == 0, len(test)



if __name__ == '__main__':
    test_class()
