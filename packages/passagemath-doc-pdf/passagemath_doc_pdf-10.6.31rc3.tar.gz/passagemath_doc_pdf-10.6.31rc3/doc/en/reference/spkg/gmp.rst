.. _spkg_gmp:

gmp: Library for arbitrary precision arithmetic
===============================================

Description
-----------

GMP is a free library for arbitrary precision arithmetic, operating on
signed integers, rational numbers, and floating-point numbers. There is
no practical limit to the precision except the ones implied by the
available memory in the machine GMP runs on. GMP has a rich set of
functions, and the functions have a regular interface.

License
-------

-  LGPL V3


Upstream Contact
----------------

-  http://gmplib.org


Type
----

standard


Dependencies
------------

- :ref:`spkg_xz`

Version Information
-------------------

package-version.txt::

    6.3.0

src/pyproject.toml::

    gmpy2 ~=2.1.b999

See https://repology.org/project/gmp/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i gmp

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add gmp-dev

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install gmp

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libgmp-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install gmp gmp-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/gmp

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-libs/gmp

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install gmp

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install gmp

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install gmp-devel

.. tab:: pyodide:

   install the following packages: libgmp

.. tab:: Slackware:

   .. CODE-BLOCK:: bash

       $ sudo slackpkg install gmp

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install gmp-devel gmpxx-devel


If the system package is installed, ``./configure`` will check if it can be used.
