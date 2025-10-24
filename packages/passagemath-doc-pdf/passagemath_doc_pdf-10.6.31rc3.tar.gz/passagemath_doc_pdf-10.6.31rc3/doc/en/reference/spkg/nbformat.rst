.. _spkg_nbformat:

nbformat: The Jupyter Notebook format
=====================================

Description
-----------

The Jupyter Notebook format

License
-------

BSD 3-Clause License

Upstream Contact
----------------

https://pypi.org/project/nbformat/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_fastjsonschema`
- :ref:`spkg_jsonschema`
- :ref:`spkg_jupyter_core`
- :ref:`spkg_pip`
- :ref:`spkg_traitlets`

Version Information
-------------------

package-version.txt::

    5.9.2

version_requirements.txt::

    nbformat >=5.0.7

See https://repology.org/project/nbformat/versions, https://repology.org/project/python:nbformat/versions, https://repology.org/project/jupyter-nbformat/versions, https://repology.org/project/python:jupyter-nbformat/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install nbformat\>=5.0.7

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i nbformat

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install nbformat

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-nbformat

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/nbformat

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install jupyter-nbformat

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-jupyter_nbformat


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
