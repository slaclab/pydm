.. _Environment:

Setting up the Environment
==========================

.. _VirtualMachine:

Virtual Machine
---------------

We provide a virtual machine disk that is the base for the application that will
be developed during this tutorial.

You can download the disk using this `Link <https://drive.google.com/a/stanford.edu/file/d/1SE4_oDF2wg_7ltKOIdJuZIqkpHzLUkbm/view?usp=sharing>`_.

Using the Downloaded Disk
^^^^^^^^^^^^^^^^^^^^^^^^^

After downloading it, extract the ``.tar.gz`` file, create a new Virtual Machine at the virtualization client of your preference.

The instructions below are for `Oracle VirtualBox <https://www.virtualbox.org/wiki/Downloads>`_ .
Oracle VirtualBox is available for Windows, OS X and Linux hosts.

This file is not a complete Virtual Machine dump that can be imported but instead a disk.

In order to use this disk, start by creating a new virtual Machine, select Type as ``Linux`` and Version as ``Ubuntu (64-bit)``.
Configure the amount of memory to use (something greater or equal 2048MB should do it.
Make sure to select ``Use an existing virtual hard disk file.`` and select the extracted ``.vmdk`` file.

.. figure:: /_static/tutorials/new_vm.png
    :scale: 100 %
    :align: center
    :alt: Create new VM


Useful Virtual Machine Information
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

User Account
++++++++++++
========    ========
Username    Password
========    ========
user        tutorial
========    ========

.. _PythonEnv:

Python Environment
++++++++++++++++++

On this machine we are using Miniconda to handle our Python environment and dependencies.
To have access to the environmnet please do:

.. code-block:: bash

    source activate tutorial

.. _IOCS:

Simulated EPICS IOCs
++++++++++++++++++++

This machine comes with simulated motors and cameras.
The IOCs can be started through their launcher scripts available at:

.. code-block:: bash

    cd ~/tutorial/iocs_launcher

    # For the AreaDetector (cameras) simulation use
    ./simDetector

    # For the simulated motor axis use
    ./simMotor

    # For the linking IOC
    ./simLinker

For AreaDetector (cameras):

-  The prefix for the PVs is ``13SIM1:`` so we have: ``13SIM1:cam1`` as well as ``13SIM1:cam2`` available.

For Motor Axis:

- The prexif for the PVs is ``IOC:`` so we have: ``IOC:m1 .. IOC:m8``


Creating your own environment
-----------------------------

If you decide to create your own environment and not use the Virtual Machine
provided please refer to the `PyDM Documentation Website <http://slaclab.github.io/pydm/>`_
for an up-to-date dependency list as well as detailed installation instructions.
