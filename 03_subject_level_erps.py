"""
=============
Preprocessing
==============

Extracts relevant data and removes artefacts.

Authors: José C. García Alanis <alanis.jcg@gmail.com>

License: BSD (3-clause)
"""
# %%
# imports
import sys
import os

import warnings

from pathlib import Path

import matplotlib.pyplot as plt

from mne.viz import plot_compare_evokeds
from mne.utils import logger
from mne.io import read_raw_fif
from mne import events_from_annotations, Epochs, open_report

from config import (
    FPATH_DATA_BIDS,
    FPATH_DATA_DERIVATIVES,
    FPATH_BIDS_NOT_FOUND_MSG,
    FPATH_BIDSDATA_NOT_FOUND_MSG,
    SUBJECT_IDS,
    BAD_SUBJECTS_SES_01,
    BAD_SUBJECTS_SES_02
)

from utils import parse_overwrite

from fooof import FOOOF
from scipy.stats import linregress
import antropy as ant
import neurokit2 as nk

# %%
# default settings (use subject 1, don't overwrite output files)
subj = 1
session = 1
overwrite = False
report = False

# %%
# When not in an IPython session, get command line inputs
# https://docs.python.org/3/library/sys.html#sys.ps1
if not hasattr(sys, "ps1"):
    defaults = dict(
        sub=subj,
        session=session,
        overwrite=overwrite,
        report=report
    )

    defaults = parse_overwrite(defaults)

    subj = defaults["sub"]
    session = defaults["session"]
    overwrite = defaults["overwrite"]
    report = defaults["report"]

# %%
# paths and overwrite settings
if subj not in SUBJECT_IDS:
    raise ValueError(f"'{subj}' is not a valid subject ID.\nUse: {SUBJECT_IDS}")

# skip bad subjects
if session == 1 and subj in BAD_SUBJECTS_SES_01:
    sys.exit()
if session == 2 and subj in BAD_SUBJECTS_SES_02:
    sys.exit()

if not os.path.exists(FPATH_DATA_BIDS):
    raise RuntimeError(
        FPATH_BIDS_NOT_FOUND_MSG.format(FPATH_DATA_BIDS)
    )

# create path for preprocessed data
subj_str = str(subj).rjust(3, '0')
FPATH_PREPROCESSED = os.path.join(FPATH_DATA_DERIVATIVES,
                                  'preprocessing',
                                  'sub-%s' % subj_str)

if not Path(FPATH_PREPROCESSED).exists():
    Path(FPATH_PREPROCESSED).mkdir(parents=True, exist_ok=True)

if overwrite:
    logger.info("`overwrite` is set to ``True`` ")

# %%
#  create path for import

# subject file id
str_subj = str(subj).rjust(3, '0')

FPATH_PREPROCESSED = os.path.join(FPATH_PREPROCESSED,
                                  'eeg',
                                  'sub-%s_task-%s_preprocessed-raw.fif' % (
                                      str_subj, 'vogel2004'))

if not os.path.exists(FPATH_PREPROCESSED):
    warnings.warn(FPATH_BIDSDATA_NOT_FOUND_MSG.format(FPATH_PREPROCESSED))
    sys.exit()

# %%
# get the data
raw = read_raw_fif(FPATH_PREPROCESSED)
raw.load_data()

# only keep eeg channels
raw.pick_types(eeg=True)
# sampling rate
sfreq = raw.info['sfreq']

# %%
# create a dictionary with event IDs for standardised handling
condition_ids = {'Stimulus/S 21': 2,
                 'Stimulus/S 41': 4,
                 'Stimulus/S 61': 6
                 }

# event codes for segmentation
event_ids = {'set_size_2': 2,
             'set_size_4': 4,
             'set_size_6': 6
             }

# extract events
events, ids = events_from_annotations(raw, event_id=condition_ids,
                                      regexp=None)

# %%
# extract set size epochs
tmin = -0.5
tmax = 1.5
set_epochs = Epochs(raw, events,
                    event_ids,
                    on_missing='ignore',
                    tmin=tmin,
                    tmax=tmax,
                    baseline=None,
                    preload=True,
                    reject_by_annotation=True,
                    reject=dict(eeg=150e-6),
                    )

# %%
# make set size erps
set_2 = set_epochs['set_size_2'].copy().apply_baseline((-0.35, -0.05)).average()
set_4 = set_epochs['set_size_4'].copy().apply_baseline((-0.35, -0.05)).average()
set_6 = set_epochs['set_size_6'].copy().apply_baseline((-0.35, -0.05)).average()

fig, ax = plt.subplots(1, 1, figsize=(16, 8))
plot_compare_evokeds({'Set size 2': set_2,
                      'Set size 4': set_4,
                      'Set size 6': set_6,},
                     picks=['47', '54'],
                     combine='mean',
                     ylim=dict(eeg=[-10, 10]),
                     invert_y=True,
                     title='Channels 47, and 54',
                     axes=ax,
                     show=False)
plt.close('all')

# %%
if report:
    FPATH_REPORT = os.path.join(FPATH_DATA_DERIVATIVES,
                                'report',
                                'sub-%s' % f'{subj:03}')

    FPATH_REPORT_I = os.path.join(
        FPATH_REPORT,
        'Subj_%s_preprocessing_report.hdf5' % f'{subj:03}')

    bidsdata_report = open_report(FPATH_REPORT_I)

    bidsdata_report.add_figure(
        fig=fig,
        title='Set size ERPs',
        image_format='PNG'
    )

    if overwrite:
        logger.info("`overwrite` is set to ``True`` ")

    for rep_ext in ['hdf5', 'html']:
        FPATH_REPORT_O = os.path.join(
            FPATH_REPORT,
            'Subj_%s_preprocessing_report.%s' % (f'{subj:03}', rep_ext))

        bidsdata_report.save(FPATH_REPORT_O,
                             overwrite=overwrite,
                             open_browser=False)
