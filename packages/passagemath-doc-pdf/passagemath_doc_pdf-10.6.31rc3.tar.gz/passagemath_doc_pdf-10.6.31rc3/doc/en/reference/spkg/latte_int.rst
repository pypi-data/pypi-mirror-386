.. _spkg_latte_int:

latte_int: Count lattice points, compute volumes, and integrate over convex polytopes
=====================================================================================

Description
-----------

LattE (Lattice point Enumeration) Integrale solves the problems of
counting lattice points in and integration over convex polytopes.

License
-------

GPLv2


Upstream Contact
----------------

Matthias Köppe, UC Davis, CA, USA

https://www.math.ucdavis.edu/~latte/

https://github.com/latte-int/latte


Type
----

optional


Dependencies
------------

- $(MP_LIBRARY)
- :ref:`spkg_4ti2`
- :ref:`spkg_cddlib`
- :ref:`spkg_lidia`
- :ref:`spkg_ntl`

Version Information
-------------------

package-version.txt::

    1.7.6

See https://repology.org/project/latte-integrale/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i latte_int

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S latte-integrale

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install latte-integrale

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install latte-integrale

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install latte


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
