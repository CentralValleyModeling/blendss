import logging
from pathlib import Path

import pandss as pdss

from .objects import Study, StudyConfig


def replace_parts(path: pdss.DatasetPath, study: Study) -> pdss.DatasetPath:
    kwargs = {
        k: getattr(study, k) or getattr(path, k)  # Default to value in the dss
        for k in ("a", "b", "c", "f")
    }
    kwargs["d"] = path.d
    kwargs["e"] = path.e
    return pdss.DatasetPath(**kwargs)


def blend(
    new_dss: Path,
    studies: StudyConfig | list[Study],
    paths: list[pdss.DatasetPath],
):
    assert isinstance(new_dss, Path)
    new_dss = new_dss.resolve()
    assert len(studies) > 0
    for study in studies:
        logging.info(f"finding data in {study.dss}")
        # For each path, search the catalog for the no-wildcard path
        with pdss.DSS(study.dss) as dss:
            catalog = dss.read_catalog()
        no_wildcard = set()
        for path in paths:
            no_wildcard = no_wildcard.union(catalog.resolve_wildcard(path).paths)
        logging.info(f"{len(no_wildcard)} paths found")
        # For all the no wildcard paths, overwrite the parts provided in the config
        new_paths = set()
        for path in no_wildcard:
            new_paths.add(replace_parts(path, study))
        logging.info(f"{len(new_paths)} paths generated")
        if len(new_paths) != len(no_wildcard):
            logging.critical("old/new paths size mis-match")
            raise ValueError(
                "The number of unique paths was reduced after replacing A-F parts,"
                + " there is no longer a 1 to 1 relationship between old paths and new"
                + " paths that does not cause data to be overwritten in the resulting"
                + " dss."
            )
        logging.info(f"copying data for {study}")
        pdss.copy_multiple_rts(study.dss, new_dss, zip(no_wildcard, new_paths))
