from pathlib import Path
from typing import Generator


def get_available() -> Generator[Path, None, None]:
    here = Path(__file__).parent
    for f in here.iterdir():
        if f.suffix == ".fv":
            yield f
