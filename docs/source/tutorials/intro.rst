.. _Setup:

Tutorial Setup
==========================

PCASpy Server
---------------

A `PCASpy <https://pcaspy.readthedocs.io/en/latest/>`_ server provides the PVs used by the 
application developed during this tutorial.

The server mimics some PVs of a motor and camera, and is located as follows:
 .. code-block:: bash

    examples/testing_ioc/pydm-tutorial-ioc

Running 'pip install -r requirements.txt' provides all needed prerequisites.

Using the PCASpy Server
^^^^^^^^^^^^^^^^^^^^^^^^^

Run the server as follows:
 .. code-block:: bash

    export EPICS_CA_MAX_ARRAY_BYTES=10000000
    ./examples/testing_ioc/pydm-tutorial-ioc

In another terminal window, enable the sever's running state:
 .. code-block:: bash

    caput MTEST:Run 1

The server will now be running and the tutorial can access the necessary PV's.

In another (third) terminal window, completed tutorial files can be ran as follows:
 .. code-block:: bash

    export EPICS_CA_MAX_ARRAY_BYTES=10000000
    pydm <tutorial_file_name>.ui|.py