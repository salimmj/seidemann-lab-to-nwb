# seidemann-lab-to-nwb
NWB conversion scripts for Seidemann lab data to the [neuro data without borders](https://www.nwb.org/) data format.

## Clone and dev install
To run the following repo you need to have installed both git and pip then do the following.

```
$ git clone https://github.com/catalystneuro/seidemann-lab-to-nwb
$ pip install -e .
```

Alternatively, to clone the repository and set up a conda environment, do:
```
$ git clone https://github.com/catalystneuro/seidemann-lab-to-nwb
$ cd nwb-conversion-tools
$ conda env create --file make_env.yml
$ conda activate seidemann-lab-to-nwb-env
```

## Repository structure
Each conversion is organized in a directory of its own in the `src` directory:

    seidemann-lab-to-nwb/
    ├── LICENSE
    ├── make_env.yml
    ├── pyproject.toml
    ├── README.md
    ├── requirements.txt
    ├── setup.py
    └── src
        ├── seidemann_lab_to_nwb
        │   ├── conversion_directory_1
        │   └── embargo20a`
        │       ├── embargo20abehaviorinterface.py
        │       ├── embargo20a_convert_script.py
        │       ├── embargo20a_metadata.yml
        │       ├── embargo20anwbconverter.py
        │       ├── embargo20a_requirements.txt
        │       └── __init__.py
        │   ├── conversion_directory_b

        └── __init__.py

 For example, for the conversion `embargo20a` you can find a directory located in `src/seidemann-lab-to-nwb/embargo20a`. Inside each conversion directory you can find the following files:

* `embargo20a_convert_script.py`: this is the cemtral script that you must run in order to perform the full conversion.
* `embargo20a_requirements.txt`: dependencies specific to this conversion specifically.
* `embargo20a_metadata.yml`: metadata in yaml format for this specific conversion.
* `embargo20abehaviorinterface.py`: the behavior interface. Usually ad-hoc for each conversion.
* `embargo20anwbconverter.py`: The place where the `NWBConverter` class is defined.

The directory might contain other files that are necessary for the conversion but those are the central ones.

## Running a specific conversion
To run a specific conversion, you might need to install first some conversion specific dependencies that are located in each conversion directory:
```
pip install -r src/seidemann_lab_to_nwb/embargo20a/embargo20a_requirements.txt 
```

You can run a specific conversion with the following command:
```
python src/seidemann_lab_to_nwb/embargo20a/embargo20a_conversion_script.py
```
