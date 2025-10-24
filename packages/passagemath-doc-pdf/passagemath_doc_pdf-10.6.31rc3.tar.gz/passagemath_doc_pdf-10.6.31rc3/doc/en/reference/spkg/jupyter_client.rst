.. _spkg_jupyter_client:

jupyter_client: Jupyter protocol implementation and client libraries
====================================================================

Description
-----------

Jupyter protocol implementation and client libraries

License
-------

BSD 3-Clause License

Upstream Contact
----------------

https://pypi.org/project/jupyter-client/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_dateutil`
- :ref:`spkg_importlib_metadata`
- :ref:`spkg_jupyter_core`
- :ref:`spkg_pip`
- :ref:`spkg_pyzmq`
- :ref:`spkg_tornado`
- :ref:`spkg_traitlets`

Version Information
-------------------

package-version.txt::

    8.6.3

src/pyproject.toml::

    jupyter-client

version_requirements.txt::

    jupyter-client

See https://repology.org/project/jupyter-client/versions, https://repology.org/project/python:jupyter-client/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install jupyter-client

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i jupyter_client

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install jupyter_client

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-jupyter-client

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/jupyter_client

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-jupyter_client

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-jupyter-client

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-jupyter_client


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
