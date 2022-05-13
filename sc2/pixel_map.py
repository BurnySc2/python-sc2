from typing import Callable, FrozenSet, List, Set

import numpy as np

from sc2.position import Point2


class PixelMap:

    def __init__(self, proto, in_bits: bool = False, mirrored: bool = False):
        """
        :param proto:
        :param in_bits:
        :param mirrored:
        """
        self._proto = proto
        # Used for copying pixelmaps
        self._in_bits: bool = in_bits
        self._mirrored: bool = mirrored

        assert self.width * self.height == (8 if in_bits else 1) * len(
            self._proto.data
        ), f"{self.width * self.height} {(8 if in_bits else 1)*len(self._proto.data)}"
        buffer_data = np.frombuffer(self._proto.data, dtype=np.uint8)
        if in_bits:
            buffer_data = np.unpackbits(buffer_data)
        self.data_numpy = buffer_data.reshape(self._proto.size.y, self._proto.size.x)
        if mirrored:
            self.data_numpy = np.flipud(self.data_numpy)

    @property
    def width(self):
        return self._proto.size.x

    @property
    def height(self):
        return self._proto.size.y

    @property
    def bits_per_pixel(self):
        return self._proto.bits_per_pixel

    @property
    def bytes_per_pixel(self):
        return self._proto.bits_per_pixel // 8

    def __getitem__(self, pos):
        """ Example usage: is_pathable = self._game_info.pathing_grid[Point2((20, 20))] != 0 """
        assert 0 <= pos[0] < self.width, f"x is {pos[0]}, self.width is {self.width}"
        assert 0 <= pos[1] < self.height, f"y is {pos[1]}, self.height is {self.height}"
        return int(self.data_numpy[pos[1], pos[0]])

    def __setitem__(self, pos, value):
        """ Example usage: self._game_info.pathing_grid[Point2((20, 20))] = 255 """
        assert 0 <= pos[0] < self.width, f"x is {pos[0]}, self.width is {self.width}"
        assert 0 <= pos[1] < self.height, f"y is {pos[1]}, self.height is {self.height}"
        assert (
            0 <= value <= 254 * self._in_bits + 1
        ), f"value is {value}, it should be between 0 and {254 * self._in_bits + 1}"
        assert isinstance(value, int), f"value is of type {type(value)}, it should be an integer"
        self.data_numpy[pos[1], pos[0]] = value

    def is_set(self, p):
        return self[p] != 0

    def is_empty(self, p):
        return not self.is_set(p)

    def copy(self):
        return PixelMap(self._proto, in_bits=self._in_bits, mirrored=self._mirrored)

    def flood_fill(self, start_point: Point2, pred: Callable[[int], bool]) -> Set[Point2]:
        nodes: Set[Point2] = set()
        queue: List[Point2] = [start_point]

        while queue:
            x, y = queue.pop()

            if not (0 <= x < self.width and 0 <= y < self.height):
                continue

            if Point2((x, y)) in nodes:
                continue

            if pred(self[x, y]):
                nodes.add(Point2((x, y)))
                queue += [Point2((x + a, y + b)) for a in [-1, 0, 1] for b in [-1, 0, 1] if not (a == 0 and b == 0)]
        return nodes

    def flood_fill_all(self, pred: Callable[[int], bool]) -> Set[FrozenSet[Point2]]:
        groups: Set[FrozenSet[Point2]] = set()

        for x in range(self.width):
            for y in range(self.height):
                if any((x, y) in g for g in groups):
                    continue

                if pred(self[x, y]):
                    groups.add(frozenset(self.flood_fill(Point2((x, y)), pred)))

        return groups

    def print(self, wide=False):
        for y in range(self.height):
            for x in range(self.width):
                print("#" if self.is_set((x, y)) else " ", end=(" " if wide else ""))
            print("")

    def save_image(self, filename):
        data = [(0, 0, self[x, y]) for y in range(self.height) for x in range(self.width)]
        # pylint: disable=C0415
        from PIL import Image

        im = Image.new("RGB", (self.width, self.height))
        im.putdata(data)  # type: ignore
        im.save(filename)

    def plot(self):
        # pylint: disable=C0415
        import matplotlib.pyplot as plt

        plt.imshow(self.data_numpy, origin="lower")
        plt.show()
