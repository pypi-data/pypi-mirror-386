.. _spkg_cython:

cython: C-Extensions for Python, an optimizing static compiler
==============================================================

Description
-----------

Cython is a language that makes writing C extensions for the Python
language as easy as Python itself. Cython is based on the well-known
Pyrex, but supports more cutting edge functionality and optimizations.

The Cython language is very close to the Python language, but Cython
additio- nally supports calling C functions and declaring C types on
variables and class attributes. This allows the compiler to generate
very efficient C code from Cython code.

This makes Cython the ideal language for wrapping for external C
libraries, and for fast C modules that speed up the execution of Python
code.


License
-------

Apache License, Version 2.0


Upstream Contact
----------------

-  http://www.cython.org/

-  cython-devel@python.org


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_pythran`

Version Information
-------------------

package-version.txt::

    3.1.5

src/pyproject.toml::

    cython >=3.0.8, <3.2.0
    cython >=3.0.8,<3.2.0

version_requirements.txt::

    cython

See https://repology.org/project/python:cython/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install cython\>=3.0.8\,\<3.2.0 cython\>=3.0.8\,\<3.2.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i cython

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S cython

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install cython\>=3.0\,\!=3.0.3\,\<4.0

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install cython3

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-cython

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install lang/cython

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/cython

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install cython

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-cython

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-Cython

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-Cython


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
