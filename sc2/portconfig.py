import json
import portpicker

class Portconfig:
    def __init__(self):
        self.shared = portpicker.pick_unused_port()
        self.server = [portpicker.pick_unused_port() for _ in range(2)]
        self.players = [[portpicker.pick_unused_port() for _ in range(2)] for _ in range(2)]

    def __str__(self):
        return f"Portconfig(shared={self.shared}, server={self.server}, players={self.players})"

    @property
    def as_json(self):
        return json.dumps({"shared": self.shared, "server": self.server, "players": self.players})

    @classmethod
    def from_json(cls, json_data):
        self = cls.__new__(cls)
        data = json.loads(json_data)
        self.shared = data["shared"]
        self.server = data["server"]
        self.players = data["players"]
        return self
