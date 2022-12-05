"""
===========================
Create sourcedata directory
===========================

Put EEG data files in subject specific directory structure
for easier porting to EEG-BIDS.

Authors: José C. García Alanis <alanis.jcg@gmail.com>

License: BSD (3-clause)
"""
# %%
# imports
import sys
import os
from pathlib import Path
import shutil

from mne.utils import logger

from config import (
    FPATH_DATA_RAW,
    FPATH_RAW_NOT_FOUND_MSG,
    FNAME_RAW_VHDR_SES_1_TEMPLATE,
    FNAME_RAW_VHDR_SES_2_TEMPLATE,
    FNAME_SOURCEDATA_TEMPLATE,
    FNAME_SOURCEDATA_PILOTS,
    SUBJECT_IDS
)

from utils import parse_overwrite

# %%
# default settings (use subject 1, don't overwrite output files)
subj = 1
session = 1
overwrite = False

# %%
# When not in an IPython session, get command line inputs
# https://docs.python.org/3/library/sys.html#sys.ps1
if not hasattr(sys, "ps1"):
    defaults = dict(
        sub=subj,
        session=session,
        overwrite=overwrite,
    )

    defaults = parse_overwrite(defaults)

    subj = defaults["sub"]
    session = defaults["session"]
    overwrite = defaults["overwrite"]

# %%
# paths and overwrite settings
if subj not in SUBJECT_IDS:
    raise ValueError(f"'{subj}' is not a valid subject ID.\nUse: {SUBJECT_IDS}")

if not os.path.exists(FPATH_DATA_RAW):
    raise RuntimeError(FPATH_RAW_NOT_FOUND_MSG.format(FPATH_DATA_RAW))
if overwrite:
    logger.info("`overwrite` is set to ``True`` "
                "but has been disabled in this script.")

# %%
# get raw data files and move them to subject (and session) specific directories

# path to raw data
if session == 1:
    if subj == 77:
        fname_raw = os.path.join(FPATH_DATA_RAW, 'Test0077_ML.vhdr')
    elif subj == 99:
        fname_raw = os.path.join(FPATH_DATA_RAW, 'Test0099.vhdr')
    else:
        fname_raw = FNAME_RAW_VHDR_SES_1_TEMPLATE.format(subj=subj)
    # path to new sourcedata directory
    # subj 77 has a weird name (account for that)
    if subj == 77:
        fname_sourcedata = FNAME_SOURCEDATA_PILOTS.format(
            subj=subj,
            session=session,
            ext='_ML.vhdr'
        )
    elif subj == 99:
        fname_sourcedata = FNAME_SOURCEDATA_PILOTS.format(
            subj=subj,
            session=session,
            ext='.vhdr'
        )
    else:
        fname_sourcedata = FNAME_SOURCEDATA_TEMPLATE.format(
            subj=subj,
            session=session,
            ext='.vhdr'
        )
elif session == 2:
    fname_raw = FNAME_RAW_VHDR_SES_2_TEMPLATE.format(subj=subj)
    fname_sourcedata = FNAME_SOURCEDATA_TEMPLATE.format(
        subj=subj,
        session=session,
        ext='_2.vhdr'
    )
else:
    raise RuntimeError("Invalid session number provided. Session number"
                       " must be 1 or 2.")

if os.path.isfile(fname_sourcedata):
    logger.info("subject %s, session %s already in %s \n"
                "Skipping." % (subj, session, Path(fname_sourcedata).parent))
    sys.exit(0)

# check if directory exists (if not created; no overwrite)
Path(fname_sourcedata).parent.mkdir(parents=True, exist_ok=True)

if Path(fname_raw).exists():
    fnames_raw = [
        fname_raw.split('.')[0] + ext
        for ext in ['.vhdr', '.eeg', '.vmrk']
    ]
    fnames_sourcedata = [
        fname_sourcedata.split('.')[0] + ext
        for ext in ['.vhdr', '.eeg', '.vmrk']
    ]

    for raw, sourcedata in zip(fnames_raw, fnames_sourcedata):
        print(raw, ' -> ',  sourcedata)
        shutil.move(raw, sourcedata)
