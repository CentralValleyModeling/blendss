import argparse
import logging
from pathlib import Path

import pandss as pdss
from pandas import read_csv

TOML_SECTION_TEMPLATE = """[[paths]]
name="{name}"
path="{path}"
category="{category}"
units="{units}"
period_type="{period_type}"
interval="{interval}"
detail="{detail}"
"""
logger = logging.getLogger(__name__)


def existing_file(f: str) -> Path:
    p = Path(f).resolve()
    if not p.exists():
        raise argparse.ArgumentTypeError(f"file not found: {f}\n\tresolved to: {p}")
    return p


def new_file(f: str) -> Path:
    p = Path(f).resolve()
    if p.exists():
        raise argparse.ArgumentTypeError(f"file exists: {f}\n\tresolved to: {p}")
    return p


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CLI to create an empty fv.toml file from an fv file."
    )

    parser.add_argument(
        "src",
        help="The fv file to convert",
        type=existing_file,
    )
    parser.add_argument(
        "--dss",
        help="If provided, metadata like 'units' will be filled in when creating the"
        + " toml file, otherwise it will remain empty.",
        default=None,
        type=existing_file,
    )
    parser.add_argument(
        "--dst",
        help="The output toml file.",
        default=None,
        type=new_file,
    )
    return parser.parse_args()


def cli() -> None:
    logger.info("create_toml_from_fv.cli called")
    args = parse_arguments()
    logger.info(args)
    src: Path = args.src
    dst: Path = args.dst or src.with_name(src.stem + "-fv.toml")
    dss: Path | None = args.dss
    main(src=src, dst=dst, dss=dss)
    logger.info("done")


def read_fv(src: Path) -> list[pdss.DatasetPath]:
    logger.info(f"reading fv file: {src}")
    df = read_csv(src, sep=r"\t", engine="python")
    df.columns = ["B", "C"]
    paths = list()
    for _, row in df.iterrows():
        paths.append(pdss.DatasetPath(b=str(row["B"]), c=str(row["C"])))
    return paths


def read_dss(
    dss: Path,
    paths: list[pdss.DatasetPath],
) -> dict[pdss.DatasetPath, dict[str, str]]:
    logger.info("reading dss file for fv file contexts")
    logger.info(f"context for {len(paths):,} paths read from {dss=}")
    context = dict()
    with pdss.DSS(dss) as dss_obj:
        for path in paths:
            try:
                rts = dss_obj.read_rts(path, expect_single=True)
                context[rts.path] = {
                    "path": rts.path,
                    "units": rts.units,
                    "interval": rts.interval,
                    "period_type": rts.period_type,
                }
            except pdss.errors.DatasetNotFound:
                logger.warning(
                    f"couldn't find {path=},"
                    + " defaulting to no additional context for this path"
                )
                context[path] = {}
            except pdss.errors.UnexpectedDSSReturn:
                logger.warning(
                    f"{path=} returned an unexpected result,"
                    + " defaulting to no additional context for this path"
                )
                context[path] = {}

    return context


def main(src: Path, dst: Path, dss: Path) -> None:
    logger.info("create_toml_from_fv.main called")
    logger.info(f"{str(src)} -> {str(dst)}")
    paths = read_fv(src)
    if dss:
        logger.info(f"reading additional metadata from {str(dss)}")
        # this context dict will have fully resolved paths
        context = read_dss(dss, paths)
    else:
        logger.info("no dss given, the toml will be empty of most metadata")
        # empty, but makes it so we can loop over this object
        context = {p: {} for p in paths}
    logger.info("assembling sections")
    sections = list()
    for p in context:
        kwargs = {
            "name": p.b,
            "path": str(p),
            "category": "",
            "units": "",
            "period_type": "",
            "interval": "",
            "detail": "",
        }
        kwargs.update(context[p])
        sections.append(TOML_SECTION_TEMPLATE.format(**kwargs))
    logger.info("writing toml")
    with open(dst, "w") as DST:
        # Write a header
        DST.write("#" * 72 + "\n")
        DST.write(
            "# This toml file was automatically created by the blendss utility.\n"
        )
        DST.write("# This file contains paths and their metadata from an `fv` file.\n")
        DST.write(f"# The original `fv` file was: {str(src)}\n")
        if dss:
            DST.write(f"# Additional metadata was added by reading: {str(dss)}\n")
        DST.write("#" * 72 + "\n\n")
        # Write the content
        DST.write("\n".join(sections))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s - %(asctime)s - %(message)s",
    )
    logger.setLevel(logging.INFO)
    cli()
