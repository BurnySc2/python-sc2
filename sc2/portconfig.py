import json
import portpicker


class Portconfig:
    """
    A data class for ports used by participants to join a match.

    EVERY participant joining the match must send the same sets of ports to join successfully.
    SC2 needs 2 ports per connection (one for data, one as a 'header'), which is why the ports come in pairs.

    :param guests: number of non-hosting participants in a match (i.e. 1 less than the number of participants)
    :param server_ports: [int portA, int portB]
    :param player_ports: [[int port1A, int port1B], [int port2A, int port2B], ... ]

    .shared is deprecated, and should TODO be removed soon (once ladderbots' __init__.py doesnt specify them).

    .server contains the pair of ports used by the participant 'hosting' the match

    .players contains a pair of ports for every 'guest' (non-hosting participants) in the match
    E.g. for 1v1, there will be only 1 guest. For 2v2 (coming soonTM), there would be 3 guests.
    """
    def __init__(self, guests=1, server_ports=None, player_ports=None):
        self.shared = None
        self._picked_ports = []
        if server_ports:
            self.server = server_ports
        else:
            self.server = [portpicker.pick_unused_port() for _ in range(2)]
            self._picked_ports.extend(self.server)
        if player_ports:
            self.players = player_ports
        else:
            self.players = [[portpicker.pick_unused_port() for _ in range(2)] for _ in range(guests)]
            self._picked_ports.extend(port for player in self.players for port in player)

    def clean(self):
        while self._picked_ports:
            portpicker.return_port(self._picked_ports.pop())

    def __str__(self):
        return f"Portconfig(shared={self.shared}, server={self.server}, players={self.players})"

    @property
    def as_json(self):
        return json.dumps({"shared": self.shared, "server": self.server, "players": self.players})

    @classmethod
    def from_json(cls, json_data):
        data = json.loads(json_data)
        return Portconfig(server_ports=data["server"], player_ports=data["players"])
