.. _spkg_fplll:

fplll: Lattice algorithms, including LLL with floating-point orthogonalization
==============================================================================

Description
-----------

fplll contains implementations of several lattice algorithms. The
implementation relies on floating-point orthogonalization, and LLL is
central to the code, hence the name.

Website: https://github.com/fplll/fplll

License
-------

-  LGPL V2.1+


Upstream Contact
----------------

-  Martin Albrecht <martinralbrecht+fplll@googlemail.com>
-  Mailing List https://groups.google.com/forum/#!forum/fplll-devel


Type
----

standard


Dependencies
------------

- $(MP_LIBRARY)
- :ref:`spkg_mpfr`

Version Information
-------------------

package-version.txt::

    5.5.0

See https://repology.org/project/fplll/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i fplll

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S fplll

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install fplll

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libfplll-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install libfplll libfplll-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/fplll

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge sci-libs/fplll

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install fplll

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install pkgconfig\(fplll\) fplll-devel fplll

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install fplll-devel


If the system package is installed, ``./configure`` will check if it can be used.
