import logging
from collections import Counter
from pathlib import Path
from typing import Iterable

import pandss as pdss

from .objects import Study, StudyConfig


def resolve_wildcards(
    study: Study,
    paths: Iterable[pdss.DatasetPath],
) -> set[pdss.DatasetPath]:
    # For each path, search the catalog for the no-wildcard path
    with pdss.DSS(study.dss) as dss:
        catalog = dss.read_catalog()
    no_wildcard = set()
    for path in paths:
        no_wildcard = no_wildcard.union(catalog.resolve_wildcard(path).paths)
    logging.info(f"{len(no_wildcard)} paths found")
    return no_wildcard


def replace_parts(
    study: Study,
    path: pdss.DatasetPath,
) -> pdss.DatasetPath:
    kwargs = {
        k: getattr(study, k) or getattr(path, k)  # Default to value in the dss
        for k in ("a", "b", "c", "f")
    }
    kwargs["d"] = path.d
    kwargs["e"] = path.e
    return pdss.DatasetPath(**kwargs)


def generate_new_paths(
    study: Study,
    paths: Iterable[pdss.DatasetPath],
) -> set[pdss.DatasetPath]:
    # For all the paths, overwrite the parts provided in the config
    new_paths = set()
    for path in paths:
        new_paths.add(replace_parts(study, path))
    logging.info(f"{len(new_paths)} paths generated")
    return new_paths


def blend(
    new_dss: Path,
    studies: StudyConfig | list[Study],
    paths: list[pdss.DatasetPath],
):
    logging.info(f"blending {len(studies)} dss files")
    assert isinstance(new_dss, Path), "argument new_path should be type pathlib.Path"
    new_dss = new_dss.resolve()
    assert len(studies) > 0, ""
    all_paths = list()
    for study in studies:
        logging.info(f"finding data in {study.dss}")
        no_wildcard = resolve_wildcards(study, paths)
        new_paths = generate_new_paths(study, no_wildcard)
        all_paths.extend(new_paths)  # Save these for error checking later
        # Check to make sure changing the names didn't cause a collision within one file
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
    # Do some error checking and issue warnings
    set_all_paths = set(all_paths)
    if len(all_paths) != len(set_all_paths):
        logging.warning("name collisions occurred, data was not transferred to new dss")
        counts = Counter(all_paths)
        for p in set_all_paths:
            if counts[p] != 1:
                logging.warning(f"{p} had a name collision and was overwritten.")
