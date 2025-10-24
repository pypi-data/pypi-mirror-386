.. _spkg_packaging:

packaging: Core utilities for Python packages
=============================================

Description
-----------

Core utilities for Python packages

License
-------

Upstream Contact
----------------

https://pypi.org/project/packaging/



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

    25.0

version_requirements.txt::

    packaging >=24.2

See https://repology.org/project/packaging/versions, https://repology.org/project/python:packaging/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install packaging\>=24.2

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i packaging

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-packaging

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install packaging

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-packaging

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-packaging

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/packaging

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-packaging

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-packaging

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-packaging


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
