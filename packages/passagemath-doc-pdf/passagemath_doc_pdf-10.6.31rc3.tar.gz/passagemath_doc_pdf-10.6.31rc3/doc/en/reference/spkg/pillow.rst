.. _spkg_pillow:

pillow: Python Imaging Library
==============================

Description
-----------

Pillow is the "friendly" PIL fork by Alex Clark and Contributors.

The Python Imaging Library (PIL) adds powerful image processing and
graphics capabilities to Python. The library supports many file formats.

License
-------

Standard PIL License


Upstream Contact
----------------

- Author: Alex Clark <aclark@aclark.net>
- https://python-pillow.org/
- Homepage: http://python-imaging.github.io/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_freetype`
- :ref:`spkg_pkgconf`
- :ref:`spkg_zlib`

Version Information
-------------------

package-version.txt::

    11.2.1.p0

src/pyproject.toml::

    pillow >=7.2.0

version_requirements.txt::

    pillow

See https://repology.org/project/python:pillow/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pillow\>=7.2.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pillow

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-pillow

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install pillow

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-pillow

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-pillow

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/pillow

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install pillow

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-Pillow

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-Pillow

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-Pillow


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
