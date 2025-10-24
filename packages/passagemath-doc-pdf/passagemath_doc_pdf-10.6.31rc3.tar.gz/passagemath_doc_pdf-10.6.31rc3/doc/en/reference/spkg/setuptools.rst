.. _spkg_setuptools:

setuptools: Build system for Python packages
============================================

Description
-----------

setuptools is the classical build system for Python packages,
a collection of enhancements to the Python distutils.

License
-------

MIT License

Upstream Contact
----------------

http://pypi.python.org/pypi/setuptools/

https://github.com/pypa/setuptools


Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    78.1.0

src/pyproject.toml::

    setuptools >= 77.0.0

version_requirements.txt::

    setuptools

See https://repology.org/project/python:setuptools/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install setuptools\>=77.0.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i setuptools

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-setuptools

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install setuptools

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-setuptools

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-setuptools

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/setuptools

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-setuptools

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-setuptools

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-setuptools


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
