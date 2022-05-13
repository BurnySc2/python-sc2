from pathlib import Path

from sc2.main import get_replay_version

THIS_FOLDER = Path(__file__).parent
REPLAY_PATHS = [path for path in (THIS_FOLDER / 'replays').iterdir() if path.suffix == '.SC2Replay']


def test_get_replay_version():
    for replay_path in REPLAY_PATHS:
        version = get_replay_version(replay_path)
        assert version == ('Base86383', '22EAC562CD0C6A31FB2C2C21E3AA3680')
