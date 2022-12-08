# eegml-vnm-cda

The pipeline relies on the brain imaging data structure ([BIDS](https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/03-electroencephalography.html)) for electroencephalography data.

BIDS helps organize datasets in an intuitive and well documented manner.

This analysis pipeline takes BIDS formatted data as an input. The pipeline then carries a series of standardised preprocessing and analysis steps and stores the results a BIDS compliant directory structure.

Your data needs to be in BIDS format ([see below](#1-put-data-in-a-bids-compliant-directory-structure) for details on how to make a BIDS dataset) for the pipeline to run.

If you already have your data in BIDS format then you can go to [2. Preprocessing and analysis](#2-preprocessing-and-analysis).

## Analysis scripts

The pipeline has multiple scrips (e.g., `00_restructure_eeg_data_directory.py`). The numbers at the beginning of the file name show the order in which they should be run.

The files `00_restructure_eeg_data_directory.py` and `01_data_to_bids.py` can be used to turn an (ordinary) dataset into a BIDS dataset.

## 1. Put data in a BIDS compliant directory structure

You'll need to create the paths for the project.
That includes all BIDS paths needed for storing the BIDS conform version of the data.

The script `set_paths.py` will get you started. It will create a `paths.json` file containing the important paths (see the provided `paths.json` file for an example).

- First, downloaded this repository (e.g., as .zip and unpack).
- Second, put your data in a `data/raw` directory within the downloaded version of the repo.
  - The file structure should look something like this:

```
|eegml-vnm-cda/
|--- data/
|----- raw/
|-------- Test0077_ML.eeg 
|-------- Test0077_ML.vhdr
|-------- ...
|-------- Test0099.eeg
|-------- Test0099.vhdr
|-------- ...
|--- .gitignore
|--- README
|--- 00_restructure_eeg_data_directory.py 
|--- 01_data_to_bids.py
|--- config.py
...
```

  - As you can see, there can be multiple subjects in the `data/raw` directory.

- Third, run the `00_restructure_eeg_data_directory.py` to restructure the data into a *more* BIDS conform directory structure. The scripts can be run from the command line as follows:
  - The scrips have arguments (e.g., subject ID; see scripts for detail) that can be specified while in each call.
  - This allows running the script for several subjects as in the call below.

```shell
for i in 77 99
do
    python 00_restructure_eeg_data_directory.py \
        --subj=$i \
        --overwrite=True
done
```

- Forth, run the `01_data_to_bids.py`. The script will create all a `bidsdata/` derectory containing all EEG-Files in an EEG-BIDS compliant dataset structure.

## 2. Preprocessing and analysis

File `02_run_preprocessing.py` takes the BIDS formatted data and runs a minimal preprocessing pipeline.
- Discard pauses between blocks and resting state.
- Filter (0.01 - 80 Hz) + periodic notch filter (50 Hz, 100 Hz)
- Infomax ICA + standardised removal of artefact components (based on correlation with EOG component templates)

File `03_subject_level_erps.py`
- Segment data around set size markers (rejects epochs with amplitudes > 200 micro-volt)
- Make ERP figures
  - The signal is low-pass filtered (40Hz, 10Hz transition bandwidth) prior to plotting.

Setting the argument `--report=True` will create a small html-report for the subject (see below).

```shell
for i in 77 99
do
    python 03_subject_level_erps.py \
        --subj=$i \
        --report=True \
        --overwrite=True
done
```

## Requirements

You'll need the following packages:

```
mne:              1.1.1
numpy:            1.22.4
scipy:            1.8.1
matplotlib:       3.5.2
mne_bids:         0.10
mne_qt_browser:   0.3.1
```

The structure of the pipeline is inspired by [Stefan Appelhoff's](https://github.com/sappelhoff) EEG analysis [repository](https://github.com/sappelhoff/eeg_manypipes_arc).
