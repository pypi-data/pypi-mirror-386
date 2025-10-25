# H5py Wrappers (H5pyWrappers)

[![Test library](https://github.com/mrfitzpa/h5pywrappers/actions/workflows/test_library.yml/badge.svg)](https://github.com/mrfitzpa/h5pywrappers/actions/workflows/test_library.yml)
[![Code Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/mrfitzpa/6c0ddb605956db582842599ae0dbad81/raw/h5pywrappers_coverage_badge.json)](https://github.com/mrfitzpa/h5pywrappers/actions/workflows/measure_code_coverage.yml)
[![Documentation](https://img.shields.io/badge/docs-read-brightgreen)](https://mrfitzpa.github.io/h5pywrappers)
[![PyPi Version](https://img.shields.io/pypi/v/h5pywrappers.svg)](https://pypi.org/project/h5pywrappers)
[![Conda-Forge Version](https://img.shields.io/conda/vn/conda-forge/h5pywrappers.svg)](https://anaconda.org/conda-forge/h5pywrappers)
[![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

`h5pywrappers` is a simple Python library that contains several functions used
to facilitate loading data from and saving data to HDF5 files. These functions
are wrappers that call functions from the
[`h5py`](https://docs.h5py.org/en/stable/) library.

Visit the `h5pywrappers` [website](https://mrfitzpa.github.io/h5pywrappers) for
a web version of the installation instructions, the reference guide, and the
examples archive.

The source code can be found in the [`h5pywrappers` GitHub
repository](https://github.com/mrfitzpa/h5pywrappers).



## Table of contents

- [Instructions for installing and uninstalling
  `h5pywrappers`](#instructions-for-installing-and-uninstalling-h5pywrappers)
  - [Installing `h5pywrappers`](#installing-h5pywrappers)
    - [Installing `h5pywrappers` using
      `pip`](#installing-h5pywrappers-using-pip)
    - [Installing `h5pywrappers` using
      `conda`](#installing-h5pywrappers-using-conda)
  - [Uninstalling `h5pywrappers`](#uninstalling-h5pywrappers)
- [Learning how to use `h5pywrappers`](#learning-how-to-use-h5pywrappers)



## Instructions for installing and uninstalling `h5pywrappers`



### Installing `h5pywrappers`

For all installation scenarios, first open up the appropriate command line
interface. On Unix-based systems, you could open e.g. a terminal. On Windows
systems you could open e.g. an Anaconda Prompt as an administrator.



#### Installing `h5pywrappers` using `pip`

Before installing `h5pywrappers`, make sure that you have activated the
(virtual) environment in which you intend to install said package. After which,
simply run the following command:

    pip install h5pywrappers

The above command will install the latest stable version of `h5pywrappers`.

To install the latest development version from the main branch of the
[h5pywrappers GitHub repository](https://github.com/mrfitzpa/h5pywrappers), one
must first clone the repository by running the following command:

    git clone https://github.com/mrfitzpa/h5pywrappers.git

Next, change into the root of the cloned repository, and then run the following
command:

    pip install .

Note that you must include the period as well. The above command executes a
standard installation of `h5pywrappers`.

Optionally, for additional features in `h5pywrappers`, one can install
additional dependencies upon installing `h5pywrappers`. To install a subset of
additional dependencies (along with the standard installation), run the
following command from the root of the repository:

    pip install .[<selector>]

where `<selector>` can be one of the following:

* `tests`: to install the dependencies necessary for running unit tests;
* `examples`: to install the dependencies necessary for executing files stored
  in `<root>/examples`, where `<root>` is the root of the repository;
* `docs`: to install the dependencies necessary for documentation generation;
* `all`: to install all of the above optional dependencies.

Alternatively, one can run:

    pip install h5pywrappers[<selector>]

elsewhere in order to install the latest stable version of `h5pywrappers`, along
with the subset of additional dependencies specified by `<selector>`.



#### Installing `h5pywrappers` using `conda`

To install `h5pywrappers` using the `conda` package manager, run the following
command:

    conda install -c conda-forge h5pywrappers

The above command will install the latest stable version of `h5pywrappers`.



### Uninstalling `h5pywrappers`

If `h5pywrappers` was installed using `pip`, then to uninstall, run the
following command:

    pip uninstall h5pywrappers

If `h5pywrappers` was installed using `conda`, then to uninstall, run the
following command:

    conda remove h5pywrappers



## Learning how to use `h5pywrappers`

For those new to the `h5pywrappers` library, it is recommended that they take a
look at the [Examples](https://mrfitzpa.github.io/h5pywrappers/examples.html)
page, which contain code examples that show how one can use the `h5pywrappers`
library. While going through the examples, readers can consult the [h5pywrappers
reference
guide](https://mrfitzpa.github.io/h5pywrappers/_autosummary/h5pywrappers.html)
to understand what each line of code is doing.