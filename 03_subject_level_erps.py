"""
==========================
Subject-level ERP analysis
==========================

Extracts condition specific segments, computes ERPs, and generates figures.

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

# import numpy as np

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

# %%
# default settings (use subject 1, don't overwrite output files)
subj = 1
session = 1
overwrite = False
report = False
jobs = 1

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

# add mastoid reference
raw.set_eeg_reference(['29', '28'])

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
                    reject=dict(eeg=200e-6),
                    )

# filter epochs for visualisation
set_epochs = set_epochs.filter(l_freq=None, h_freq=40.0,
                               picks=['eeg'],
                               filter_length='auto',
                               l_trans_bandwidth='auto',
                               h_trans_bandwidth='auto',
                               method='fir',
                               phase='zero',
                               fir_window='hamming',
                               fir_design='firwin',
                               n_jobs=jobs)

# %%
# make set size erps
set_2 = set_epochs['set_size_2'].copy().apply_baseline((-0.20, 0.00)).average()
set_4 = set_epochs['set_size_4'].copy().apply_baseline((-0.20, 0.00)).average()
set_6 = set_epochs['set_size_6'].copy().apply_baseline((-0.20, 0.00)).average()

# channels to plot
channels_right = ['39', '40', '46']
channels_left = ['15', '16', '24']

# make ERP figure
plt.rcParams.update({'font.size': 14})
fig_erp, ax = plt.subplots(2, 1, figsize=(15, 15))
for n_roi, channels in enumerate([channels_right, channels_left]):
    if int(channels[0]) < 32:
        roi = 'Left'
    else:
        roi = 'Right'

    plot_compare_evokeds({'Set size 2': set_2,
                          'Set size 4': set_4,
                          'Set size 6': set_6, },
                         picks=channels,
                         combine='mean',
                         ylim=dict(eeg=[-10, 10]),
                         invert_y=True,
                         title='% s channels: %s' % (roi, ', '.join(
                             str(ch) for ch in channels)),
                         axes=ax[n_roi],
                         show=False)
fig_erp.subplots_adjust(hspace=0.5)
plt.close('all')

# # make topomap figure
# plt.rcParams.update({'font.size': 14})
# fig_topo, ax = plt.subplots(3, 9, figsize=(15, 15))
# for n_set, set_size in enumerate([set_2, set_4, set_6]):
#     set_size.plot_topomap(times=np.arange(0.1, 1.0, 0.1),
#                           vmin=-10, vmax=10, axes=ax[n_set, :],
#                           colorbar=False)

# %%
if report:
    FPATH_REPORT = os.path.join(FPATH_DATA_DERIVATIVES,
                                'report',
                                'sub-%s' % f'{subj:03}')

    FPATH_REPORT_I = os.path.join(
        FPATH_REPORT,
        'Subj_%s_preprocessing_report.hdf5' % f'{subj:03}')

    bidsdata_report = open_report(FPATH_REPORT_I)

    if 'epochs' in bidsdata_report.tags and overwrite:
        bidsdata_report.remove(title='Set size ERPs')

    bidsdata_report.add_figure(
        fig=fig_erp,
        tags='epochs',
        title='Set size ERPs',
        section='epochs',
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
