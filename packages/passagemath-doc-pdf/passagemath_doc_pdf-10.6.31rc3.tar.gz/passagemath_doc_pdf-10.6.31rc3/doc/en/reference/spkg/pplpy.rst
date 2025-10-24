.. _spkg_pplpy:

pplpy: Python interface to the Parma Polyhedra Library
======================================================

Description
-----------

PPL Python wrapper

The Python package pplpy provides a wrapper to the C++ Parma Polyhedra
Library (PPL).

The whole package started as a fork of a tiny part of the Sage library.

We are using the compatible fork passagemath-ppl.

License
-------

GPL version 3


Upstream Contact
----------------

-  https://github.com/passagemath/passagemath-ppl


Type
----

standard


Dependencies
------------

- $(MP_LIBRARY)
- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cysignals`
- :ref:`spkg_cython`
- :ref:`spkg_gmpy2`
- :ref:`spkg_mpc`
- :ref:`spkg_mpfr`
- :ref:`spkg_ppl`

Version Information
-------------------

package-version.txt::

    0.8.10.1

version_requirements.txt::

    passagemath-ppl

See https://repology.org/project/pplpy/versions, https://repology.org/project/python:pplpy/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-ppl

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pplpy

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-pplpy

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install pplpy

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-pplpy

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/py-pplpy

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/pplpy

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-pplpy


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
