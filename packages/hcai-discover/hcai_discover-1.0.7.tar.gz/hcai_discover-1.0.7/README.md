# DISCOVER - A Modular Software Framework for Human Behavior Analysis


## Overview

DISCOVER is an open-source software framework designed to facilitate computational-driven data exploration in human behavior analysis. This user-friendly and modular platform streamlines complex methodologies, enabling researchers across disciplines to engage in detailed behavioral analysis without extensive technical expertise.

Key Features

* Modularity: DISCOVER's modular architecture allows for easy integration of new features and customization.
* User-Friendliness: Intuitive interface simplifies the data exploration process, making it accessible to non-technical users.
* Flexibility: Supports a wide range of data types and analysis workflows.
* Scalability: Handles large datasets with ease.

Use Cases

* Interactive Semantic Content Exploration
* Visual Inspection
* Aided Annotation
* Multimodal Scene Search

## Getting Started

DISCOVER provides a set of blueprints for exploratory data analysis, serving as a starting point for researchers to engage in detailed behavioral analysis.

### Prerequesites

Before starting to install DISCOVER you need to install Python and FFMPEG.
While other Python versions may work as well the module is only tested for the following versions:

* 3.9.x
* 3.10.x
* 3.11.x

You can download the current version of python for your system [here](https://www.python.org/downloads/).

Download the current version off FFMPEG binaries from [here](https://github.com/BtbN/FFmpeg-Builds/releases) for your system and make sure to extract them to a place that is in your system path.
It is recommended to setup a separate virtual environment to isolate the NOVA server installation from your system python installation.
To do so, open a terminal at the directory where your virtual environment should be installed and paste the following command:

```python -m venv discover-venv```

You can then activate the virtual environment like this:

```.\discover-venv\Scripts\activate```

### Setup

Install DISCOVER using pip like this:

```pip install hcai-discover```

### Start the server

To start DISCOVER you just open a Terminal and type

```discover```

DISCOVER takes the following optional arguments as input:

```
--env: '' : Path to a dotenv file containing your server configuration

--host: 0.0.0.0 : The IP for the Server to listen

--port : 8080 : The port for the Server to be bound to

--cml_dir : cml : The cooperative machine learning directory containing DISCOVER modules (available at: https://github.com/hcmlab/discover-modules)

--data_dir : data : Directory where the data resides

--cache_dir : cache : Cache directory for Models and other downloadable content

--tmp_dir : tmp : Directory to store data for temporary usage

--log_dir : log : Directory to store logfiles.

--use_tls : Enable TLS/SSL for HTTPS connections (requires certificates)
```

Internally DISCOVER converts the input to environment variables with the following names: 

```DISCOVER_HOST```, ```DISCOVER_PORT```, ```DISCOVER_CML_DIR```, ```DISCOVER_DATA_DIR```, ```DISCOVER_CACHE_DIR```, ```DISCOVER_TMP_DIR```, ```DISCOVER_LOG_DIR```, ```DISCOVER_USE_TLS```


All variables can be either passed directly as commandline argument, set in a [dotenv](https://hexdocs.pm/dotenvy/dotenv-file-format.html) file or as system wide environment variables.
During runtime the arguments will be prioritized in this order commandline arguments -> dotenv file -> environment variable -> default value.

If the server started successfully your console output should look like this:
```
Starting DISCOVER v1.0.0...
HOST: 0.0.0.0
PORT: 8080
DISCOVER_CML_DIR : cml
DISCOVER_DATA_DIR : data
DISCOVER_CACHE_DIR : cache
DISCOVER_TMP_DIR : tmp
DISCOVER_LOG_DIR : log
...done
DISCOVER HTTP server starting on 0.0.0.0:8080
```

### Modules

DISCOVER modules contain the machine learning models and processing pipelines. You can get the official modules from:

**https://github.com/hcmlab/discover-modules**

Clone or download the modules repository and set the `--cml_dir` parameter to point to the modules directory.

You can find the full documentation of the project [here](https://hcmlab.github.io/discover).

## Citation
If you use DISCOVER consider citing the following paper: 

```
@article{schiller2024discover,
title={DISCOVER: A Data-driven Interactive System for Comprehensive Observation, Visualization, and ExploRation of Human Behaviour},
author={Schiller, Dominik and Hallmen, Tobias and Withanage Don, Daksitha and Andr{\'e}, Elisabeth and Baur, Tobias},
journal={arXiv e-prints},
pages={arXiv--2407},
year={2024}
}
```