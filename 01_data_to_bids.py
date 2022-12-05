"""
===========================
Source data set to EEG BIDS
===========================

Put EEG data into a BIDS-compliant directory structure.

Authors: José C. García Alanis <alanis.jcg@gmail.com>

License: BSD (3-clause)
"""
# %%
# imports
import sys
import os

import re

from mne.io import read_raw_brainvision
from mne.utils import logger

from mne_bids import BIDSPath, write_raw_bids

from config import (
    FPATH_DATA_SOURCEDATA,
    FNAME_SOURCEDATA_PILOTS,
    FPATH_DATA_BIDS,
    FPATH_SOURCEDATA_NOT_FOUND_MSG,
    FNAME_SOURCEDATA_TEMPLATE,
    SUBJECT_IDS,
    CHECK_SUBJECTS_SES_01,
    montage
)

from utils import parse_overwrite

# %%
# default settings (use subject 1, don't overwrite output files)
subj = 1
session = 1
overwrite = False
ext = '.vhdr'

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

if not os.path.exists(FPATH_DATA_SOURCEDATA):
    raise RuntimeError(
        FPATH_SOURCEDATA_NOT_FOUND_MSG.format(FPATH_DATA_SOURCEDATA)
    )
if overwrite:
    logger.info("`overwrite` is set to ``True`` ")

# %%
# path to file in question (i.e., which subject and session)
if session == 1:
    if subj == 77:
        fname = FNAME_SOURCEDATA_PILOTS.format(
            subj=subj,
            session=session,
            ext='_ML.vhdr'
        )
    elif subj == 99:
        fname = FNAME_SOURCEDATA_PILOTS.format(
            subj=subj,
            session=session,
            ext='.vhdr'
        )
    else:
        fname = FNAME_SOURCEDATA_TEMPLATE.format(
            subj=subj,
            session=session,
            ext=ext
        )
    if subj in CHECK_SUBJECTS_SES_01:
        # subject 116 does not comply with naming convention due to
        # typo in name --> this fixes that
        if subj == 116:
            # remove the wrong name from string
            fname = re.sub('_0116', '_00116', fname)

elif session == 2:
    ext = '_2' + ext
    fname = FNAME_SOURCEDATA_TEMPLATE.format(
        subj=subj,
        session=session,
        ext=ext
    )
else:
    raise RuntimeError("Invalid session number provided. Session number"
                       " must be 1 or 2.")

# %%
# 1) import the data
raw = read_raw_brainvision(fname,
                           eog=['32', '63', '64'],
                           preload=False)
# get sampling frequency
sfreq = raw.info['sfreq']

# add custom sensor positions and fiducials
raw.set_montage(montage)

# %%
# 2) export to bids

# create bids path
run = 1
output_path = BIDSPath(subject=f'{subj:03}',
                       task='multiple',
                       session=str(session),
                       run=run,
                       datatype='eeg',
                       root=FPATH_DATA_BIDS)
# write file
write_raw_bids(raw,
               output_path,
               montage=None,
               overwrite=True)

# %%
# 3) check for subjects with more than one file.
# Due to technical problems some sessions had to be saved in
# two different files
add_file = False
if session == 1:
    if subj in CHECK_SUBJECTS_SES_01:
        if subj == 116:
            sys.exit()
        else:
            ext = '_' + CHECK_SUBJECTS_SES_01[subj].split(',')[-2].split('_')[-1]
            run = CHECK_SUBJECTS_SES_01[subj].split(',')[-1].split(' ')[-1]
            fname = FNAME_SOURCEDATA_TEMPLATE.format(
                subj=subj,
                session=session,
                ext=ext
            )
            if subj == 119:
                fname = re.sub('_0119_', '_', fname)
            add_file = True

elif session == 2:
    if subj == 6:
        ext = '_2_2.vhdr'
        fname = FNAME_SOURCEDATA_TEMPLATE.format(
            subj=subj,
            session=session,
            ext=ext
        )
        add_file = True

if add_file:
    # run BIDS transform for second file
    raw = read_raw_brainvision(fname,
                               eog=['vEOG_o', 'vEOG_u'],
                               preload=False)
    sfreq = raw.info['sfreq']
    raw.set_montage(montage)
    # create bids path
    output_path = BIDSPath(subject=f'{subj:03}',
                           task='multiple',
                           session=str(session),
                           run=int(run),
                           datatype='eeg',
                           root=FPATH_DATA_BIDS)
    # write file
    write_raw_bids(raw,
                   output_path,
                   overwrite=True)
