.. _installation_instructions_sec:

Instructions for installing and uninstalling ``embeam``
=======================================================



Installing ``embeam``
---------------------

For all installation scenarios, first open up the appropriate command line
interface. On Unix-based systems, you could open e.g. a terminal. On Windows
systems you could open e.g. an Anaconda Prompt as an administrator.



Installing ``embeam`` using ``pip``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before installing ``embeam``, make sure that you have activated the (virtual)
environment in which you intend to install said package. After which, simply run
the following command::

  pip install embeam

The above command will install the latest stable version of ``embeam``.

To install the latest development version from the main branch of the `embeam
GitHub repository <https://github.com/mrfitzpa/embeam>`_, one must first clone
the repository by running the following command::

  git clone https://github.com/mrfitzpa/embeam.git

Next, change into the root of the cloned repository, and then run the following
command::

  pip install .

Note that you must include the period as well. The above command executes a
standard installation of ``embeam``.

Optionally, for additional features in ``embeam``, one can install additional
dependencies upon installing ``embeam``. To install a subset of additional
dependencies (along with the standard installation), run the following command
from the root of the repository::

  pip install .[<selector>]

where ``<selector>`` can be one of the following:

* ``tests``: to install the dependencies necessary for running unit tests;
* ``examples``: to install the dependencies necessary for executing files stored
  in ``<root>/examples``, where ``<root>`` is the root of the repository;
* ``docs``: to install the dependencies necessary for documentation generation;
* ``all``: to install all of the above optional dependencies.

Alternatively, one can run::

  pip install embeam[<selector>]

elsewhere in order to install the latest stable version of ``embeam``, along
with the subset of additional dependencies specified by ``<selector>``.



Installing ``embeam`` using ``conda``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before proceeding, make sure that you have activated the (virtual) ``conda``
environment in which you intend to install said package.

To install ``embeam`` using the ``conda`` package manager, run the following
command::

  conda install -c conda-forge embeam

The above command will install the latest stable version of ``embeam``.



Uninstalling ``embeam``
-----------------------

If ``embeam`` was installed using ``pip``, then to uninstall, run the following
command from the root of the repository::

  pip uninstall embeam

If ``embeam`` was installed using ``conda``, then to uninstall, run the
following command from the root of the repository::

  conda remove embeam
