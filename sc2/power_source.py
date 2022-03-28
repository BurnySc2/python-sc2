from sc2.position import Point2


class PowerSource:

    @classmethod
    def from_proto(cls, proto):
        return cls(Point2.from_proto(proto.pos), proto.radius, proto.tag)

    def __init__(self, position, radius, unit_tag):
        assert isinstance(position, Point2)
        assert radius > 0
        self.position = position
        self.radius = radius
        self.unit_tag = unit_tag

    def covers(self, position):
        return self.position.distance_to(position) <= self.radius

    def __repr__(self):
        return f"PowerSource({self.position}, {self.radius})"


class PsionicMatrix:

    @classmethod
    def from_proto(cls, proto):
        return cls([PowerSource.from_proto(p) for p in proto])

    def __init__(self, sources):
        self.sources = sources

    def covers(self, position):
        return any(source.covers(position) for source in self.sources)
