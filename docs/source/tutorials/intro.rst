.. _Setup:

Tutorial Setup
==========================

Virtual Environment
--------------------

This tutorial will use a standard conda environment for running the example code. Please follow the installation
instructions here :ref:`pydm installation instructions<Install>` to install PyDM. Both conda and mamba will work.

Once that environment has been created, there are 2 additional packages needed for this tutorial as noted below.

Scipy
------

First install scipy into the environment created above. Scipy is used in some of the simulation code that we will
use PyDM to interact with. The versions on PyPI and conda-forge will both work, so either is fine to use:

.. code-block:: bash

  pip install scipy

Or:

.. code-block:: bash

  conda install scipy -c conda-forge


PCASpy Server
---------------

A `PCASpy <https://pcaspy.readthedocs.io/en/latest/>`_ server provides PVs for the tutorial files to read/write.

The server mimics some PVs of a motor and camera, and is located as follows:
 .. code-block:: bash

    examples/testing_ioc/pydm-tutorial-ioc

Install the PCASpy package into the environment from above, again both PyPI and conda-forge will work:

.. code-block:: bash

  pip install pcaspy

Or:

.. code-block:: bash

  conda install pcaspy -c conda-forge

Using the PCASpy Server
^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::
    You will need to export the following variable in each terminal that will run either the PCASpy server or pydm:
     .. code-block:: bash

       export EPICS_CA_MAX_ARRAY_BYTES=300000

Run the server as follows:
 .. code-block:: bash

    ./examples/testing_ioc/pydm-tutorial-ioc

In another terminal window, enable the sever's running state:
 .. code-block:: bash

    caput IOC:Run 1

The server will now be running and the tutorial files can access the necessary PV's.

In another (third) terminal window, the completed tutorial files can be ran as follows:
 .. code-block:: bash

    pydm <tutorial_file_name>.ui|.py
