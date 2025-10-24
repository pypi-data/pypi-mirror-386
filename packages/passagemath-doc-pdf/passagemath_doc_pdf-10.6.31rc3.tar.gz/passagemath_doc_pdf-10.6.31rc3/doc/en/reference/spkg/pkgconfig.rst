.. _spkg_pkgconfig:

pkgconfig: Python interface to pkg-config
=========================================

Description
-----------

Pkgconfig is a Python module to interface with the pkg-config command
line tool.

License
-------

MIT License


Upstream Contact
----------------

https://github.com/matze/pkgconfig


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_pip`
- :ref:`spkg_pkgconf`

Version Information
-------------------

package-version.txt::

    1.5.5

src/pyproject.toml::

    pkgconfig

version_requirements.txt::

    pkgconfig

See https://repology.org/project/python:pkgconfig/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pkgconfig

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pkgconfig

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-pkgconfig

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install pkgconfig

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-pkgconfig

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-pkgconfig

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install devel/py-pkgconfig

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/pkgconfig

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-pkgconfig

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install pkg-config

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-pkgconfig


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
