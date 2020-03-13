from sc2.main import SlidingTimeWindow


def test_sliding_time_window():
    stw = SlidingTimeWindow(5)

    stw.push(1.0)
    assert stw.sum == 1.0

    stw.push(1.0)
    assert stw.sum == 2.0

    stw.push(2.0)
    assert stw.sum == 4.0

    stw.push(2.0)
    assert stw.sum == 6.0

    stw.push(4.0)
    assert stw.sum == 10.0

    # now full, items start to get removed

    stw.push(4.0)
    assert stw.sum == 13.0

    stw.push(4.0)
    assert stw.sum == 16.0

    stw.push(4.0)
    assert stw.sum == 18.0
