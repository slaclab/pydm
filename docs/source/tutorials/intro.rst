.. _Setup:

Tutorial Setup
==========================

PCASpy Server
---------------

A `PCASpy <https://pcaspy.readthedocs.io/en/latest/>`_ server provides PVs for the tutorial files to read/write.

The server mimics some PVs of a motor and camera, and is located as follows:
 .. code-block:: bash

    examples/testing_ioc/pydm-tutorial-ioc

Installing PCASpy from the documentation above and following the :ref:`pydm installation instructions<Install>` provides all needed prerequisites for this tutorial.

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