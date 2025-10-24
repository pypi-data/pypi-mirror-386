.. _spkg_meson_python:

meson_python: Meson Python build backend (PEP 517)
==================================================

Description
-----------

Meson Python build backend (PEP 517)

License
-------

Upstream Contact
----------------

https://pypi.org/project/meson-python/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_meson`
- :ref:`spkg_ninja_build`
- :ref:`spkg_patchelf`
- :ref:`spkg_pip`
- :ref:`spkg_pyproject_metadata`
- :ref:`spkg_tomli`

Version Information
-------------------

package-version.txt::

    0.18.0

version_requirements.txt::

    meson-python >=0.15.0

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install meson-python\>=0.15.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i meson_python

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add py3-meson-python

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S meson-python

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install meson-python

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install meson-python

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-meson-python

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install devel/meson-python

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/meson-python

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python-meson-python

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-meson-python


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
