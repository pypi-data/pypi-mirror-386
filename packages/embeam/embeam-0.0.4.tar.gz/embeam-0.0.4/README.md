# Electron Microscopy Beam (EMBeam)

[![Test library](https://github.com/mrfitzpa/embeam/actions/workflows/test_library.yml/badge.svg)](https://github.com/mrfitzpa/embeam/actions/workflows/test_library.yml)
[![Code Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/mrfitzpa/d59cde9e9c2327d28f927c8316a1c7f4/raw/embeam_coverage_badge.json)](https://github.com/mrfitzpa/embeam/actions/workflows/measure_code_coverage.yml)
[![Documentation](https://img.shields.io/badge/docs-read-brightgreen)](https://mrfitzpa.github.io/embeam)
[![PyPi Version](https://img.shields.io/pypi/v/embeam.svg)](https://pypi.org/project/embeam)
[![Conda-Forge Version](https://img.shields.io/conda/vn/conda-forge/embeam.svg)](https://anaconda.org/conda-forge/embeam)
[![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

`embeam` is a Python library for modelling beams and lenses in electron
microscopy.

Visit the `embeam` [website](https://mrfitzpa.github.io/embeam) for a web version
of the installation instructions, the reference guide, and the examples archive.

The source code can be found in the [`embeam` GitHub
repository](https://github.com/mrfitzpa/embeam).



## Table of contents

- [Instructions for installing and uninstalling
  `embeam`](#instructions-for-installing-and-uninstalling-embeam)
  - [Installing `embeam`](#installing-embeam)
    - [Installing `embeam` using
      `pip`](#installing-embeam-using-pip)
    - [Installing `embeam` using
      `conda`](#installing-embeam-using-conda)
  - [Uninstalling `embeam`](#uninstalling-embeam)
- [Learning how to use `embeam`](#learning-how-to-use-embeam)



## Instructions for installing and uninstalling `embeam`



### Installing `embeam`

For all installation scenarios, first open up the appropriate command line
interface. On Unix-based systems, you could open e.g. a terminal. On Windows
systems you could open e.g. an Anaconda Prompt as an administrator.



#### Installing `embeam` using `pip`

Before installing `embeam`, make sure that you have activated the (virtual)
environment in which you intend to install said package. After which, simply
change into the root of the repository, and run the following command:

    pip install embeam

The above command will install the latest stable version of `embeam`.

To install the latest development version from the main branch of the [embeam
GitHub repository](https://github.com/mrfitzpa/embeam), one must first clone the
repository by running the following command:

    git clone https://github.com/mrfitzpa/embeam.git

Next, change into the root of the cloned repository, and then run the following
command:

    pip install .

Note that you must include the period as well. The above command executes a
standard installation of `embeam`.

Optionally, for additional features in `embeam`, one can install additional
dependencies upon installing `embeam`. To install a subset of additional
dependencies (along with the standard installation), run the following command
from the root of the repository:

    pip install .[<selector>]

where `<selector>` can be one of the following:

* `tests`: to install the dependencies necessary for running unit tests;
* `examples`: to install the dependencies necessary for executing files stored
  in `<root>/examples`, where `<root>` is the root of the repository;
* `docs`: to install the dependencies necessary for documentation generation;
* `all`: to install all of the above optional dependencies.

Alternatively, one can run:

    pip install embeam[<selector>]

elsewhere in order to install the latest stable version of `embeam`, along with
the subset of additional dependencies specified by `<selector>`.



#### Installing `embeam` using `conda`

To install `embeam` using the `conda` package manager, run the following
command:

    conda install -c conda-forge embeam

The above command will install the latest stable version of `embeam`.



### Uninstalling `embeam`

If `embeam` was installed using `pip`, then to uninstall, run the following
command from the root of the repository:

    pip uninstall embeam

If `embeam` was installed using `conda`, then to uninstall, run the following
command from the root of the repository:

    conda remove embeam



## Learning how to use `embeam`

For those new to the `embeam` library, it is recommended that they take a look
at the [Examples](https://mrfitzpa.github.io/embeam/examples.html) page, which
contain code examples that show how one can use the `embeam` library. While
going through the examples, readers can consult the [embeam reference
guide](https://mrfitzpa.github.io/embeam/_autosummary/embeam.html) to understand
what each line of code is doing.