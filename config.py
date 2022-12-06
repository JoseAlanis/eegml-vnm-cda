"""
========================
Study configuration file
========================

Configuration parameters and global values that will be used across scripts.

Authors: Jose C. Garcia Alanis <alanis.jcg@gmail.com>
License: MIT
"""
import os
import multiprocessing

from pathlib import Path

import numpy as np

import json

from mne.channels import make_dig_montage

# -----------------------------------------------------------------------------
# check number of available CPUs in system
jobs = multiprocessing.cpu_count()
os.environ["NUMEXPR_MAX_THREADS"] = str(jobs)

# -----------------------------------------------------------------------------
# file paths
with open("./paths.json") as paths:
    paths = json.load(paths)

# the root path of the dataset
FPATH_DATA = paths["root"]
# path to raw data (original brainvision directory)
FPATH_DATA_RAW = Path(os.path.join(FPATH_DATA, "raw"))
# path to sourcedata (restructured brainvision files)
FPATH_DATA_SOURCEDATA = Path(paths["sourcedata"])
# path to BIDS compliant directory structure
FPATH_DATA_BIDS = Path(paths["bidsdata"])
# path to derivatives
FPATH_DATA_DERIVATIVES = Path(paths["derivatives"])

# the paths raw data in brainvision format (.vhdr)
FNAME_RAW_VHDR_SES_1_TEMPLATE = os.path.join(
    str(FPATH_DATA_RAW), "Exp23_{subj:04}.vhdr"
)
FNAME_RAW_VHDR_SES_2_TEMPLATE = os.path.join(
    str(FPATH_DATA_RAW), "Exp23_{subj:04}_2.vhdr"
)

# -----------------------------------------------------------------------------
# file templates
# the path to the sourcedata directory
FNAME_SOURCEDATA_TEMPLATE = os.path.join(
    str(FPATH_DATA_SOURCEDATA),
    "sub-{subj:03}",
    "ses-{session:02}",
    "eeg",
    "Exp23_{subj:04}{ext}"
)
# template for pilot data
FNAME_SOURCEDATA_PILOTS = os.path.join(
    str(FPATH_DATA_SOURCEDATA),
    "sub-{subj:03}",
    "ses-{session:02}",
    "eeg",
    "Test{subj:04}{ext}"
)

# -----------------------------------------------------------------------------
# problematic subjects
NO_DATA_SUBJECTS = {
}
CHECK_SUBJECTS_SES_01 = {
}
# session 1 bad data
BAD_SUBJECTS_SES_01 = {
}

# session 2 bad data
BAD_SUBJECTS_SES_02 = {
}

# originally, subjects from 1 to 30, but some subjects should be excluded
pilots = np.array([77, 99])
subjects = np.arange(1, 31)

SUBJECT_IDS = np.array(
    list(
        set(np.concatenate((pilots, subjects), axis=0)) - set(NO_DATA_SUBJECTS)
    )
)

# -----------------------------------------------------------------------------
# default messages
FPATH_RAW_NOT_FOUND_MSG = (
    "Did not find the path:\n\n>>> {}\n"
    "\n>>Did you define the path to the data on your system in `config.py`? "
    "See the FPATH_RAW variable!<<\n"
)

# default messages
FPATH_SOURCEDATA_NOT_FOUND_MSG = (
    "Did not find the path:\n\n>>> {}\n"
    "\n>>Did you define the path to the data on your system in `config.py`? "
    "See the FPATH_DATA_SOURCEDATA variable!<<\n"
)

FPATH_BIDS_NOT_FOUND_MSG = (
    "Did not find the path:\n\n>>> {}\n"
    "\n>>Did you define the path to the data on your system in `config.py`? "
    "See the FPATH_DATA_BIDS variable!<<\n"
)

FPATH_BIDSDATA_NOT_FOUND_MSG = (
    "Did not find the path:\n\n>>> {}\n"
    "\n>>Did you define the path to the data on your system in `config.py`? "
    "See the FPATH_DATA_BIDS variable!<<\n"
)

FPATH_DERIVATIVES_NOT_FOUND_MSG = (
    "Did not find the path:\n\n>>> {}\n"
    "\n>>Did you define the path to the data on your system in `config.py`? "
    "See the FPATH_DATA_DERIVATIVES variable!<<\n"
)

EOG_COMPONENTS_NOT_FOUND_MSG = "No {type} ICA components found; subject {subj}"

# -----------------------------------------------------------------------------
# eeg parameters

# import eeg markers
with open("./eeg_markers.json") as eeg_markers:
    eeg_markers = json.load(eeg_markers)

# create eeg montage (old)
# montage = _read_theta_phi_in_degrees('./sensors/easycap-M7.txt',
#                                      head_size=0.1,
#                                      add_fiducials=True)

# create eeg montage
with open("./sensor_positions.json") as sensors:
    sensors = json.load(sensors)

montage = make_dig_montage(
    ch_pos=sensors["ch_pos"],
    nasion=sensors["nasion"],
    lpa=sensors["lpa"],
    rpa=sensors["rpa"],
    coord_frame=sensors["coord_frame"]
)

# -----------------------------------------------------------------------------
# templates
# import ica markers
with open("./ica_templates.json") as temp:
    ica_templates = json.load(temp)
