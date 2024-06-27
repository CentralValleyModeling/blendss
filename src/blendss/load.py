from pathlib import Path

import pandas as pd

from .objects import Study, StudyConfig


def load_fv(path: Path) -> pd.DataFrame:
    assert path.exists()
    df = pd.read_csv(path)
    assert len(df.columns) == 2
    for col in df:
        df[col] = df[col].str.strip()
    df.columns = ["B", "C"]
    return df


def load_studies(path: Path) -> list[Study]:
    return StudyConfig.from_file(path)
