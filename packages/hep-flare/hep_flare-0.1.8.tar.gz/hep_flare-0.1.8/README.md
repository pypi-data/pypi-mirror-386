[![CI](https://github.com/CamCoop1/FLARE/actions/workflows/ci.yaml/badge.svg)](https://github.com/CamCoop1/FLARE/actions/workflows/ci.yaml)
[![DOI](https://zenodo.org/badge/953801229.svg)](https://doi.org/10.5281/zenodo.15694628)


# FLARE: FCCee b2Luigi Automated Reconstruction and Event processing

Framework powered by b2luigi to enable streamlined use of MC generators and fccanalysis commandline tool.

# Install
To install the package, follow the basic install process. It is recommended you use a virtual environment. To begin, setup the fcc software from cvmfs

```
$ source /cvmfs/fcc.cern.ch/sw/latest/setup.sh
```

Create a virtual environment

```
$ python3 -m venv .venv
```

To activate the virtual environment use the following command:

```
$ source .venv/bin/activate
```

Lastly, you can install the framework to your virtual environment

If you are installing from PYPI then use
```
$ pip3 install hep-flare
```
Now your virtual environment will be setup like so:

```
(venv)$
```

# Setting Up Your Analysis

To begin, you can place all of your analysis scripting and tooling in your current working directory. However, it is standard to create an `analysis` directory to house all your scripts.

1. Your analysis stage scripts must be prefixed by which stage it is, as per the `Stages` enum in `flare/src/fcc_analysis/fcc_stages.py`. What this boils down to is your stage 1 analysis script must be named `stage1_{detailed name}.py`, likewise your final stage analysis script must be named `final_{detailed name}.py`. This is necessary as these prefixes are how the framework knows what stages need to be ran for your analysis.

2. You must not define an `inputDir` or `outputDir` variable in your analysis scripts for any stage. These are reserved for b2luigi to determine during runtime. The only exception is the very first stage or your analysis requires an `inputDir` to define where to look for the MC. The framework checks during runtime if you have accidentally added one of these variables to your scripts and lets you know what you need to change to fix it. Apart from this, you the analyst can define your analysis scripts are you usually would, including adding additional `includePaths` and so forth.

If you wish to use the batch system capabilities of flare, you will need to create a YAML file. In this yaml file you must define the `batch_system` variable here. The `batch_system` variable tells b2luigi which batch system it should attempt to submit to. You must set the `batch_system` value inside the YAML to one of the following, depending on your required batch system:

- lsf
- htcondor
- slurm
- local

Note, if `local` is set then b2luigi will not submit to the batch system instead just submitting to the head node that you are currently on. This is usually for when your batch system is not available in b2luigi or you wish to do some basic testing. An example of such a config yaml is shown below:

``` YAML
# analysis/config.yaml
batch_system : slurm
```

For more details on the available batch systems see [b2luigi Batch System Specific Settings](https://b2luigi.belle2.org/usage/batch.html?highlight=batch#batch-system-specific-settings). Note some batch systems require/allow for you to pass batch-specific arguments which can also be defined in this YAML file.

## Running Your Analysis

To run the framework you can use the handy CLI tool. To begin type the following into your terminal
```
(venv)$ flare run analysis --help
usage: flare run analysis [-h] [--name NAME] [--version VERSION] [--description DESCRIPTION] [--study-dir STUDY_DIR] [--output-dir OUTPUT_DIR] [--config-yaml CONFIG_YAML] [--mcprod]

options:
  -h, --help            show this help message and exit
  --name NAME           Name of the study
  --version VERSION     Version of the study
  --description DESCRIPTION
                        Description of the study
  --study-dir STUDY_DIR
                        Study directory path where the files for production are located
  --output-dir OUTPUT_DIR
                        The location where the output file will be produced, by default will be the current working directory
  --config-yaml CONFIG_YAML
                        Path to a YAML config file
  --mcprod              If set, also run mcproduction as part of the analysis
```

What will be returned is all the command line arguments you can pass to flare. Importantly, you can pass the path to your config YAML to the `--config-yaml` argument which will set the batch system variable. If no argument is
passed to `--config-yaml` flare will attempt to find a YAML file in your current working directory to use as. If no YAML is found and no additional arguments are parsed to the CLI, then default values set.

**NOTE**: No default `batch_system` is set, meaning you must set it in your config YAML

To run your analysis workflow you can use the following command in your terminal

``` console
(venv)$ ls
stage1_analysis.py stage2_analysis.py final_analysis.py plot_analysis.py config.yaml
(venv)$ flare run analysis --config-yaml config.yaml --name MyAnalysis --version higgs mass
```
Flare will automatically load the config.yaml along with your passed command line argument into its settings manager and it will run your analysis using the current working directory as the source of your FCC analysis stage scripts.
If you wish to be more systematic with your directory layout. You can move the FCC stages into its own directory like so:

``` console
(venv)$ mkdir studies/higgs_mass && mv *.py studies/higgs_mass/.
(venv)$ ls studies/higgs_mass
stage1_analysis.py stage2_analysis.py final_analysis.py plot_analysis.py
```
For those who read previously the CLI help documentation will know the you can set the `--study-dir` to specify where flare should look for you stage scripts.

```
(venv)$ flare run analysis --config-yaml config.yaml --name MyAnalysis --version higgs mass --study-dir studies/higgs_mass
```
If an argument for `--output-dir` is not given, then the current working directory is used. If you wish to centralise all your outputs you can either always call flare from the same working directory, or more simply, just set the `outputdir` variable inside the config YAML file.

If all of this is combersome and repeated you can define these variables in your config.yaml instead!

``` YAML
# config.yaml
# flare config
name: MyAnalysis
version: higgs mass
studydir: studies/higgs_mass

# b2luigi settings
batch_system: slurm
```
Now we can simply run the following for our analysis (assuming the config YAML is in the current working directory)
```
(venv)$ flare run analysis
```
If your config YAML is not in your current working directory, say you have a central config that you wish to always use that is a parent directory, set the `--config-yaml` argument to the path of the config

```
(venv)$ flare run analysis --config-yaml ../central_config/config.yaml
```

Lastly, you can use a combination of command line arguments and arguments in your yaml file. How this works is, flare will **ALWAYS** take the command line argument as priority, if no command line argument is passed for a given variable, it will default to the YAML file. If no value is found there, a default set of values are set by flare (this will surely cause a fright when your outputs aren't where you thought!)

For example, lets say i wanted to change the version name for one test but didn't want to change the YAML file you could run this command:

```
(venv)$ flare run analysis --version="higgs mass test"
```
This will set the version to that passed on the command line, ignoring that defined in the YAML file.

### Note
It is best practice to keep your setup in a YAML file as this will make it easily repetable and trackable by flare.


## Running New/Altered Analysis

You will notice the output data directory structure is based off the information provided by the user by the command line or via a config YAML. This is helpful as if you make changes to your analysis you can change the `version` variable inside this yaml file and this will allow b2luigi to run another analysis workflow for you. You will note that once you have ran the workflow once and it was successful you cannot run it again without changing the details. Alternatively, if you need to delete the a section or all of the preciously created data, you can delete the data and run your analysis with the exact same configuration.

# Setting Up MC Production

If MC production is required then a `mc_production` directory is needs to be created like so:

```
$ mkdir -p studies/special_mc_production/mc_production
```
Inside this directory you will need yet another YAML file that has a format like the following:

``` YAML
"$model" : "UserMCProdConfigModel"

global_prodtype: whizard

datatype:
    - list
    - of
    - datatypes
```

The details of this yaml file will be explained shortly. The definitions and layout are exact and will always be checked by Pydantic as per the \$model. It is important that you follow the template. If you do not include the $model at the stop of your MC Production config, flare will not run and instruct you to add this that line to your config yaml.

## Whizard + DelphesPythia6 Production
If you require whizard for you MC production, you will need the following:

### details.yaml

To select the whizard, we must set the `global_prodtype = whizard`. Under `datatype` you must list all the datatypes you will be generating.
The exact names are of your own choosing and can be as detailed or simple as you like. An example `details.yaml` can be seen below

``` yaml
"$model" : "UserMCProdConfigModel"

global_prodtype: whizard

datatype:
    - wzp6_ee_mumuH_Hbb_ecm240
    - wzp6_ee_mumuH_HWW_ecm240
```
## Input Files
To run the whizard + DelphesPythia6 workflow the following files must be located in the `mc_production`:

- < datatype >.sin
- card_<>.tcl
- edm4hep_<>.tcl

Where <> indicates areas where you can input your own naming conventions. The software checks for the key words and suffixes. Note that there must be a `.sin` file for each datatype. Using our example `details.yaml` from above, we would need two `.sin` files:

- wzp6_ee_mumuH_Hbb_ecm240.sin
- wzp6_ee_mumuH_HWW_ecm240.sin

**IMPORTANT:** The `< datatype >.sin` file must have its output file named `proc` (the standard inside FCC). Ensure each `.sin` file has the correct output file name. If not the software will not be able to work correctly.


## Madgraph + DelphesPythia8

### details.yaml

To select madgraph, we must set the `global_prodtype = madgraph`. Under `datatype` you must list all the datatypes you will be generating.
The exact names are of your own choosing and can be as detailed or simple as you like. An example `details.yaml` can be seen below

``` yaml
"$model" : "UserMCProdConfigModel"

global_prodtype: madgraph

datatype:
    - p8_ee_mumuH_Hbb_ecm240
    - p8_ee_mumuH_HWW_ecm240
```

## Input Files
To run the madgraph + DelphesPythia8 workflow the following files must be located in the `mc_production`:

- < datatype >_runcard.dat
- card_<>.tcl
- edm4hep_<>.tcl
- pythia_card_<>.cmd

Where <> indicates areas where you can input your own naming conventions. The software checks for the key words and suffixes. There must be a `.dat` file for each datatype. Using our example `details.yaml` from above, we would need two `.dat` files:

- p8_ee_mumuH_Hbb_ecm240_runcard.dat
- p8_ee_mumuH_HWW_ecm240_runcard.dat


**IMPORTANT:** The `pythia_card_<>.cmd` file must have the variable `Beams:LHEF = signal.lhe`. If this is
not present, the software will be unable to run the `DelphesPythia8_EDM4HEP` command.

## Pythia8

**Note:** As of version 0.1.0 Pythia8 is supported

### details.yaml

To select pythia8, we must set the `prodtype = pythia8`. Under `datatype` you must list all the datatypes you will be generating.
The exact names are of your own choosing and can be as detailed or simple as you like. An example `details.yaml` can be seen below

``` yaml
"$model" : "UserMCProdConfigModel"

global_prodtype: pythia8

datatype:
    - p8_ee_mumuH_Hbb_ecm240
    - p8_ee_mumuH_HWW_ecm240
```

## Input Files
To run the madgraph + DelphesPythia8 workflow the following files must be located in the `mc_production`:

- card_<>.tcl
- edm4hep_<>.tcl
- ++.cmd

Where <> indicates areas where you can input your own naming conventions. The software checks for the key words and suffixes. There must be a `++.cmd` file for each datatype, where `++` should be substituted with your datatype name as per the config yaml. Using our example `details.yaml` from above, we would need two `.cmd` files:

- p8_ee_mumuH_Hbb_ecm240.cmd
- p8_ee_mumuH_HWW_ecm240.cmd


## Mixed Production

If you wish to conduct a mixture of production types, then the config yaml inside `mc_production` must follow the format below:

```
"$model" : "UserMCProdConfigModel"


datatype:
    - wzp6_ee_mumuH_Hbb_ecm240:
        prodtype : whizard
    - p8_ee_WW_ecm240:
        prodtype : pythia8
    - p8_ee_ZZ_ecm240:
        prodtype : pythia8

```

Note, we no longer set the `global_prodtype` and instead set a local prodtype for each dataset. Note also our `datatype` is now a list of dictionaires instead of a list of strings. The pydantic model will check at run time if your config yaml is correctly formatted and if not, will indicate what you must change.

## Running the MC Production

Once you have selected your MC production type and ensured all input files are present adhering to naming conventions and required output file names (see **IMPORTANT** notes ) you are ready to run your MC production.

This can be done is one of two ways. If you wish to *just* produce the MC for now run the following command provided you have followed the instructions in [Install](#install)

```
(venv)$ ls
mc_production config.yaml
(venv)$ ls mc_production/
details.yaml wzp6_ee_mumuH_Hbb_ecm240.sin wzp6_ee_mumuH_HWW_ecm240.sin card_IDEA.tcl edm4hep_IDEA.tcl
(venv)$ flare run mcproduction --config-yaml config.yaml
```

If you instead wish to run the full workflow, that is from the start of MC production all the way to producing plots using `fcc plots` and provided you have followed the instructions in [Setting Up Your Analysis](#setting-up-your-analysis)

```
(venv)$ ls
mc_production config.yaml stage1_analysis.py stage2_analysis.py final_analysis.py plot_analysis.py
(venv)$ ls mc_production/
details.yaml wzp6_ee_mumuH_Hbb_ecm240.sin wzp6_ee_mumuH_HWW_ecm240.sin card_IDEA.tcl edm4hep_IDEA.tcl
(venv)$ flare run analysis --config-yaml config.yaml
```

As explained in [Running Your Analysis](#running-your-analysis) if you wish to create subdirectories to store your
various studies you can do so e.g:


```
(venv)$ ls
config.yaml studies
(venv)$ ls studies/
higgs_mass fancy_BSM_study
(venv)$ ls studies/fancy_BSM_study/
mc_production stage1_analysis.py stage2_analysis.py final_analysis.py plot_analysis.py
(venv)$ ls mc_production/
details.yaml wzp6_ee_mumuH_Hbb_ecm240.sin wzp6_ee_mumuH_HWW_ecm240.sin card_IDEA.tcl edm4hep_IDEA.tcl
(venv)$ flare run analysis --config-yaml config.yaml --study-dir studies/fancy_BSM_study/
```
