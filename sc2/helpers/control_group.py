class ControlGroup(set):
    def __init__(self, units):
        super().__init__({unit.tag for unit in units})

    def __hash__(self):
        return hash(tuple(sorted(list(self))))

    def select_units(self, units):
        return units.filter(lambda unit: unit.tag in self)

    def missing_unit_tags(self, units):
        return {t for t in self if units.find_by_tag(t) is None}

    @property
    def amount(self) -> int:
        return len(self)

    @property
    def empty(self) -> bool:
        return not self

    def add_unit(self, unit):
        self.add(unit.tag)

    def add_units(self, units):
        for unit in units:
            self.add_unit(unit)

    def remove_unit(self, unit):
        self.discard(unit.tag)

    def remove_units(self, units):
        for unit in units:
            self.discard(unit.tag)
