"""General utility functions that are re-used in different scripts."""
from os import path
from pathlib import Path

import json
import click
from mne.utils import logger

# get path to current file
parent = Path(__file__).parent.resolve()

# -----------------------------------------------------------------------------
@click.command()
@click.option("--rootpath", help="Path to parent directory containing eeg data")
@click.option("--sourcedata", default="sourcedata", type=str,
              help="Path to `sourcedata` directory")
@click.option("--bidsdata", default="bidsdata", type=str,
              help="Path to `bids_data` directory")
@click.option("--derivatives", default="derivatives", type=str,
              help="Path to `derivatives` directory")
@click.option("--relative", default=True, type=bool, help="Relative paths?")
@click.option("--overwrite", default=False, type=bool, help="Overwrite?")
def set_paths(
        rootpath,
        sourcedata,
        bidsdata,
        derivatives,
        relative,
        overwrite,
):
    """Parse inputs in case script is run from command line."""
    if relative:
        sourcedata = path.join(rootpath, sourcedata)
        bidsdata = path.join(rootpath, bidsdata)
        derivatives = path.join(rootpath, bidsdata, derivatives)
    else:
        sourcedata = sourcedata
        bidsdata = bidsdata
        derivatives = derivatives

    # collect all in dict
    path_vars = dict(
        root=rootpath,
        sourcedata=sourcedata,
        bidsdata=bidsdata,
        derivatives=derivatives,
        relative=relative,
        overwrite=overwrite
    )

    return path_vars


# write .json file containing basic set of paths needed for the study
paths = set_paths.main(standalone_mode=False)
for key, val in paths.items():
    logger.info(f"    > Setting '{key}': to -> {val}")  # noqa
if paths['overwrite']:
    with open(path.join(parent, 'paths.json'), 'w') as file:
        json.dump(paths, file, indent=2)
