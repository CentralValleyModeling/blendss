import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Generator, Self


@dataclass
class Study:
    """Data from one section of the configuration file. Contents will include a launch
    file for a calsim3

    Returns
    -------
    _type_
        _description_
    """

    dss: Path
    a: str = None
    b: str = None
    c: str = None
    f: str = None

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(dss={self.dss})"

    def __repr__(self) -> str:
        attrs = (
            f"{f.name}={getattr(self, f.name)}"
            for f in fields(self)
            if getattr(self, f.name)
        )
        s = ", ".join(attrs)

        return f"{self.__class__.__name_}({s})"


@dataclass
class StudyConfig:
    studies: list[Study] = field(default_factory=list)

    @classmethod
    def from_file(cls, path: Path) -> Self:
        assert isinstance(path, Path)
        assert path.exists()
        with open(path, "rb") as f:
            toml_data = tomllib.load(f)
            studies = []
            for i, item in enumerate(toml_data.get("study", list())):
                try:
                    study = Study(**item)
                except Exception as e:
                    raise ValueError(f"could not parse study {i} in {path}") from e
                studies.append(study)
        return cls(studies)

    def __iter__(self) -> Generator[Study, None, None]:
        yield from self.studies

    def __len__(self) -> int:
        return len(self.studies)
