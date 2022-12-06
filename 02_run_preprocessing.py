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

import numpy as np
import matplotlib.pyplot as plt

from mne import events_from_annotations
from mne.preprocessing import compute_bridged_electrodes, ICA, corrmap
from mne.utils import logger
from mne import concatenate_raws, open_report
from mne.viz import plot_bridged_electrodes

from mne_bids import BIDSPath, read_raw_bids

from config import (
    FPATH_DATA_BIDS,
    FPATH_DATA_DERIVATIVES,
    FPATH_BIDS_NOT_FOUND_MSG,
    FPATH_BIDSDATA_NOT_FOUND_MSG,
    EOG_COMPONENTS_NOT_FOUND_MSG,
    SUBJECT_IDS,
    CHECK_SUBJECTS_SES_01,
    BAD_SUBJECTS_SES_01,
    BAD_SUBJECTS_SES_02,
    eeg_markers,
    ica_templates
)

from utils import parse_overwrite

# from pyprep.prep_pipeline import PrepPipeline

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
# create bids path for import

# subject file id
str_subj = str(subj).rjust(3, '0')
# run file id
run = 1
if subj in CHECK_SUBJECTS_SES_01:
    run = int(CHECK_SUBJECTS_SES_01[subj].split(',')[-1].split(' ')[-1])

bids_fname = BIDSPath(root=FPATH_DATA_BIDS,
                      subject=str_subj,
                      task='vogel2004',
                      session='1',
                      run=run,
                      datatype='eeg',
                      extension='.vhdr')
if not os.path.exists(bids_fname):
    warnings.warn(FPATH_BIDSDATA_NOT_FOUND_MSG.format(bids_fname))
    sys.exit()

# %%
# get the data
raw = read_raw_bids(bids_fname)
raw.load_data()

# get sampling rate
sfreq = raw.info['sfreq']

# %%
# extract task relevant events
ses = 'ses-%s' % session
session_ids = eeg_markers[ses]
markers = session_ids['vogel2004']['markers']

# standardise event codes for import
event_ids = {'Stimulus/S%s' % str(ev).rjust(3): ev for ev in markers.values()}

# search for desired events in the data
events, events_found = events_from_annotations(raw, event_id=event_ids)

# %%
# extract the desired section of recording (only odd-even task)

# set start and end markers (session 1)
start_end = ['Stimulus/S 10', 'Stimulus/S 90']

# time relevant to those events
tmin = events[events[:, 2] == events_found[start_end[0]], 0] / sfreq - 10
if subj == 99:
    # subject 99 (pilot) has a missing start marker at beginning of experiment
    tmin = np.concatenate(([0], tmin), axis=0)
tmax = events[events[:, 2] == events_found[start_end[1]], 0] / sfreq + 6

# extract data
raw_task_bl1 = raw.copy().crop(tmin=float(tmin[1]), tmax=float(tmax[1]))
raw_task_bl2 = raw.copy().crop(tmin=float(tmin[2]), tmax=float(tmax[2]))
raw_task_bl3 = raw.copy().crop(tmin=float(tmin[3]), tmax=float(tmax[3]))
raw_task_bl4 = raw.copy().crop(tmin=float(tmin[4]), tmax=float(tmax[4]))
raw_task_bl5 = raw.copy().crop(tmin=float(tmin[5]), tmax=float(tmax[5]))
del raw

raw_task = concatenate_raws([raw_task_bl1,
                             raw_task_bl2,
                             raw_task_bl3,
                             raw_task_bl4,
                             raw_task_bl5])

del raw_task_bl1, raw_task_bl2, raw_task_bl3, raw_task_bl4, raw_task_bl5

# %%

# # check for electrode bridges
# bridged_idx, ed_matrix = compute_bridged_electrodes(raw_task)
#
# # create figure
# fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12, 4))
# fig.suptitle('Subject %s, %s\nElectrical Distance Matrix' % (subj, task))
#
# # take median across epochs, only use upper triangular, lower is NaNs
# ed_plot = np.zeros(ed_matrix.shape[1:]) * np.nan
# triu_idx = np.triu_indices(ed_plot.shape[0], 1)
# for idx0, idx1 in np.array(triu_idx).T:
#     ed_plot[idx0, idx1] = np.nanmedian(ed_matrix[:, idx0, idx1])
#
# # plot full distribution color range
# im1 = ax1.imshow(ed_plot, aspect='auto',
#                  vmin=0.0, vmax=np.nanmax(ed_plot).round(-1),
#                  cmap='Blues')
# cax1 = fig.colorbar(im1, ax=ax1)
# cax1.set_label(r'Electrical Distance ($\mu$$V^2$)')
#
# # plot zoomed in colors
# im2 = ax2.imshow(ed_plot, aspect='auto',
#                  vmin=0, vmax=10.0,
#                  cmap='Reds_r')
# cax2 = fig.colorbar(im2, ax=ax2)
# cax2.set_label(r'Potentially problematic elec. distance ($\mu$$V^2$)')
# for ax in (ax1, ax2):
#     ax.set_xlabel('Channel Index')
#     ax.set_ylabel('Channel Index')
#
# # plot topomap
# plot_bridged_electrodes(
#     raw_task.info, bridged_idx, ed_matrix,
#     title='Potentially bridged sensors',
#     topomap_args=dict(vmax=10.0, sensors=False,
#                       cmap='Greys_r', axes=ax3, show=False))
# plt.close('all')
# fig.tight_layout()
#
# # create path
# FPATH_BRIDGES = os.path.join(
#     FPATH_DATA_DERIVATIVES,
#     'preprocessing',
#     'sub-%s' % str_subj,
#     'bridging',
#     'sub-%s_task-%s_bridged-electrodes.png' % (str_subj, task))
#
# # check if directory exists
# if not Path(FPATH_BRIDGES).exists():
#     Path(FPATH_BRIDGES).parent.mkdir(parents=True, exist_ok=True)
#
# # save bridges figure
# fig.savefig(FPATH_BRIDGES, dpi=100, facecolor='white')

# %%
# apply filter to data
raw_task = raw_task.filter(l_freq=0.1, h_freq=40.0,
                           picks=['eeg', 'eog'],
                           filter_length='auto',
                           l_trans_bandwidth='auto',
                           h_trans_bandwidth='auto',
                           method='fir',
                           phase='zero',
                           fir_window='hamming',
                           fir_design='firwin',
                           n_jobs=8)

# # %%
# # make a copy of the data in question
# raw_copy = raw_task.copy()
#
# # set up prep pipeline
# prep_params = {
#     "ref_chs": "eeg",
#     "reref_chs": "eeg",
#     "line_freqs": [50, 100],
# }
# # run data through preprocessing pipeline
# montage = raw_copy.get_montage()
# prep = PrepPipeline(raw_copy, prep_params, montage, ransac=False)
# prep.fit()
#
# # %%
# # crate summary for PyPrep output
# bad_channels = {'interpolated_chans': prep.interpolated_channels,
#                 'still_noisy': prep.still_noisy_channels,
#                 'ransac': prep.ransac_settings}
#
# # %%
# # export summary to .json
#
# # create path
# FPATH_BADS = os.path.join(FPATH_DATA_DERIVATIVES,
#                           'preprocessing',
#                           'sub-%s' % str_subj,
#                           'bad_channels',
#                           '%s_task-%s_bad_channels.json' % (str_subj, task))
# # chekc if directory exists
# if not Path(FPATH_BADS).exists():
#     Path(FPATH_BADS).parent.mkdir(parents=True, exist_ok=True)
# # save file
# with open(FPATH_BADS, 'w') as bads_file:
#     json.dump(bad_channels, bads_file, indent=2)
#
# # %%
# # extract the re-referenced eeg data
# clean_raw = prep.raw.copy()
# del prep, raw_task, raw_copy
#
# # interpolate any remaining bad channels
# clean_raw.interpolate_bads()

# add average reference
clean_raw = raw_task.copy()
clean_raw = clean_raw.set_eeg_reference(projection=True)
clean_raw.apply_proj()
del raw_task

# apply notch filter (50Hz)
line_noise = [50., 100.]
clean_raw = clean_raw.notch_filter(freqs=line_noise, n_jobs=8)

# %%
# prepare ICA

# filter data to remove drifts
raw_filt = clean_raw.copy().filter(l_freq=1.0, h_freq=None, n_jobs=8)

# set ICA parameters
method = 'infomax'
fit_params=dict(extended=True)
reject = dict(eeg=250e-6)
ica = ICA(n_components=0.951,
          method=method,
          fit_params=fit_params)

# run ICA
ica.fit(raw_filt,
        reject=reject,
        reject_by_annotation=True)

# %%
# look for components that show high correlation with the artefact templates
try:
    # lower the correlation threshold for subject 14
    # (allows corrmap to select 2 components for vertical eye movements)
    if subj == 999:
        threshold = 0.85
    else:
        threshold = 'auto'
    corrmap([ica],
            template=np.array(ica_templates['vertical_eye']),
            threshold=threshold, label='vertical_eog', show=False)
    plt.close('all')
except:
    logger.info(
        EOG_COMPONENTS_NOT_FOUND_MSG.format(
            type='vertical eye movement',
            subj=subj)
    )
finally:
    logger.info("\nDone looking for vertical eye movement components\n")

try:
    # raise the correlation threshold for subject 14
    # (makes corrmap very strict about potential horizontal eye movements
    # components)
    if subj == 999:
        threshold = 0.90
    else:
        threshold = 'auto'
    corrmap([ica],
            template=np.array(ica_templates['horizontal_eye']),
            label='horizontal_eog', show=False, threshold=threshold)
    plt.close('all')
except:
    logger.info(
        EOG_COMPONENTS_NOT_FOUND_MSG.format(
            type='horizontal eye movement',
            subj=subj)
    )
finally:
    logger.info("\nDone looking for horizontal eye movement components\n")

# %%
# get the identified components and exclude them
bad_components = []
for label in ica.labels_:
    if subj != 999:
        # only take the first component that was identified by the template
        bad_components.extend([ica.labels_[label][0]])
    else:
        # only take the first component that was identified by the template
        bad_components.extend(ica.labels_[label])
logger.info('\n Found bad components:\n %s' % bad_components)

# add bad components to exclusion list
ica.exclude = list(np.unique(bad_components))


# %%
# remove the identified components and save preprocessed data
ica.apply(clean_raw)

# create path for preprocessed dara
FPATH_PREPROCESSED = os.path.join(
    FPATH_DATA_DERIVATIVES,
    'preprocessing',
    'sub-%s' % str_subj,
    'eeg',
    'sub-%s_task-%s_preprocessed-raw.fif' % (str_subj, 'vogel2004'))
# check if directory exists
if not Path(FPATH_PREPROCESSED).exists():
    Path(FPATH_PREPROCESSED).parent.mkdir(parents=True, exist_ok=True)

# save file
clean_raw.save(FPATH_PREPROCESSED, overwrite=overwrite)

# %%
if report:
    FPATH_REPORT = os.path.join(FPATH_DATA_DERIVATIVES,
                                'report',
                                'sub-%s' % f'{subj:03}')

    FPATH_REPORT_I = os.path.join(
        FPATH_REPORT,
        'Subj_%s_preprocessing_report.hdf5' % f'{subj:03}')

    bidsdata_report = open_report(FPATH_REPORT_I)

    fig = ica.plot_components(show=False)
    plt.close('all')

    bidsdata_report.add_figure(
        fig=fig, title='ICA cleaning',
        caption='Identified EOG components: %s' % ', '.join(str(x) for x in bad_components),
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

