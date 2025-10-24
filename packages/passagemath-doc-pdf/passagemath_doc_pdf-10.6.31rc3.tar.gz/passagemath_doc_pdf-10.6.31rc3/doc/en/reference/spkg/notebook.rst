.. _spkg_notebook:

notebook: Jupyter notebook, a web-based notebook environment for interactive computing
======================================================================================

Description
-----------

The Jupyter HTML notebook is a web-based notebook environment for
interactive computing.

License
-------

BSD 3-Clause License

Upstream Contact
----------------

https://pypi.org/project/notebook/


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_jupyter_server`
- :ref:`spkg_jupyterlab`
- :ref:`spkg_jupyterlab_server`
- :ref:`spkg_notebook_shim`
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    7.1.1

version_requirements.txt::

    notebook >=6.1.1

See https://repology.org/project/python:notebook/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install notebook\>=6.1.1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i notebook

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S jupyter-notebook

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install notebook

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-notebook

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/notebook

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-notebook

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-jupyter_notebook


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
