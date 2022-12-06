# eegml-vnm-cda

The pipeline has multiple scrips (e.g., `00_restructure_eeg_data_directory.py`). The numbers at the beginning of the file name show the order in which they should be run.

You'll need to create the paths for the project.
That includes all BIDS paths needed for storing the BIDS conform version of the data.

The script `set_paths.py` get you started. It will create a `paths.json` file containing the important paths (see the provided `paths.json` file for an example).

- First, downloaded this repository (e.g., as .zip and unpack).
- Second, put your data in a `data/raw` within the downloaded version of the repo.
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

The structure of the pipeline is inspired by [Stefan Appelhoff's](https://github.com/sappelhoff) EEG analysis [repository](https://github.com/sappelhoff/eeg_manypipes_arc).
