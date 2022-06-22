from __future__ import annotations

from pathlib import Path

from loguru import logger

from sc2.file_paths import Paths

MAP_FILE_EXTENSION = "SC2Map"


# Deprecated retained for backwards compatibility
def get(name: str) -> MapPath:
    return MapPath(name)


class MapPath:
    def __init__(self, name: str):
        self.path = self.get_path(name)

        if self.path.is_absolute():
            try:
                self.relative_path = self.path.relative_to(Paths.MAPS)
            except ValueError:  # path not relative to basedir
                logger.warning(f"Using absolute path: {self.path}")
                self.relative_path = self.path
        else:
            self.relative_path = self.path

    @property
    def name(self):
        return self.path.stem

    @property
    def data(self):
        with open(self.path, "rb") as f:
            return f.read()

    def __repr__(self):
        return f"Map({self.path})"

    @classmethod
    def is_map_file(cls, file: Path) -> bool:
        return file.is_file() and file.suffix == ".SC2Map"

    @classmethod
    def matches_target_map_name(cls, file: Path, name: str) -> bool:
        return cls.is_map_file(file) and file.stem == name

    def get_path(self, name: str) -> Path:
        if name:
            file_handler = Path(name)
            if file_handler.exists():
                return file_handler

            if MAP_FILE_EXTENSION not in name:
                file_handler = Path(f"{name}.{MAP_FILE_EXTENSION}")
                if file_handler.exists():
                    return file_handler

        # Iterate through 2 folder depths
        # TODO: Replace with os.walk()?
        for map_dir in iter(Paths.MAPS.iterdir()):
            if map_dir.is_dir():
                for map_file in iter(map_dir.iterdir()):
                    if self.matches_target_map_name(map_file, name):
                        return Path(map_file)
            elif self.matches_target_map_name(map_dir, name):
                return Path(map_dir)

        raise FileNotFoundError(f"Map {name} not found")
