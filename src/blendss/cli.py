import argparse
import logging
from pathlib import Path

import pandss as pdss

from . import __version__
from .blend import blend
from .load import load_fv, load_studies


def file_exists(path: str) -> Path:
    # assume given as a  full path
    p = Path(path).resolve()
    if p.exists():
        return p
    # try looking in the module
    p = Path(__file__).parent.resolve() / path
    if p.exists():
        return p
    # could not be found
    raise argparse.ArgumentTypeError(f"{path} does not exist")


def file_new(path: str) -> Path:
    p = Path(path).resolve()
    if p.exists():
        raise argparse.ArgumentTypeError(f"{path} already exists")
    return p


def parse_arguments():
    here = Path(__file__).parent
    parser = argparse.ArgumentParser(
        description="Utility for combining multiple DSS files that contain similar data"
    )

    parser.add_argument(
        "studies",
        metavar="studies",
        type=file_exists,
        help="Location of the study config file (toml format).",
    )

    parser.add_argument(
        "--newdss",
        metavar="newdss",
        type=file_new,
        default=Path("compiled.dss").resolve(),
        help="Location of the new dss file.",
    )

    parser.add_argument(
        "--fv",
        default=here / "fv" / "standard_paths.fv",
        type=file_exists,
        help="Location of the fv configuration file (default: paths.fv)",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        help="Show the conda-prefix-replacement version number and exit.",
        version="blendss %s" % __version__,
    )

    args = parser.parse_args()

    return args


def cli():
    logging.basicConfig(level=logging.INFO)
    args = parse_arguments()
    for arg, val in vars(args).items():
        logging.info(f"{arg}={val}")
    # Load data, and run script
    df_fv = load_fv(args.fv)
    studies = load_studies(args.studies)
    paths = [
        pdss.DatasetPath(b=row["B"], c=row["C"])  # convert dataframe to path
        for _, row in df_fv.iterrows()
    ]

    blend(args.newdss, studies, paths)


if __name__ == "__main__":
    cli()
