.. _spkg_singular_jupyter:

singular_jupyter: Jupyter kernel for Singular
=============================================

Description
-----------

This is a Jupyter kernel for Singular.

License
-------

GPL version 2 or later


Upstream Contact
----------------

-  https://github.com/sebasguts/jupyter_kernel_singular
-  https://pypi.org/project/passagemath-singular-jupyterkernel/


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_ipython`
- :ref:`spkg_ipywidgets`
- :ref:`spkg_jupyter_client`
- :ref:`spkg_pip`
- :ref:`spkg_sagemath_singular`

Version Information
-------------------

package-version.txt::

    0.9.9.1

version_requirements.txt::

    passagemath-singular-jupyterkernel

See https://repology.org/project/jupyter-singular/versions, https://repology.org/project/python:jupyter-kernel-singular/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-singular-jupyterkernel

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i singular_jupyter

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install jupyter-kernel-singular

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-jupyter-kernel-singular


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
