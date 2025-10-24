.. _spkg_singular:

singular: Computer algebra system for polynomial computations, algebraic geometry, singularity theory
=====================================================================================================

Description
-----------

Singular is a computer algebra system for polynomial computations, with
special emphasis on commutative and non-commutative algebra, algebraic
geometry, and singularity theory.

License
-------

GPLv2 or GPLv3

Upstream Contact
----------------

libsingular-devel@mathematik.uni-kl.de

https://www.singular.uni-kl.de/

Special Update/Build Instructions
---------------------------------

Other notes:

-  If the environment variable SAGE_DEBUG is set to "yes", then
   omalloc will be replaced by xalloc. The resulting Singular executable
   and libsingular library will be slower than with omalloc, but allow
   for easier debugging of memory corruptions.


Type
----

standard


Dependencies
------------

- $(MP_LIBRARY)
- :ref:`spkg_cddlib`
- :ref:`spkg_flint`
- :ref:`spkg_mpfr`
- :ref:`spkg_ntl`
- :ref:`spkg_readline`

Version Information
-------------------

package-version.txt::

    4.4.1p4

See https://repology.org/project/singular/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i singular

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S singular

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install singular

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install singular singular-doc libsingular4-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install Singular Singular-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/singular

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge sci-mathematics/singular\[readline\]

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install singular

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install singular

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr singular

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install singular


If the system package is installed, ``./configure`` will check if it can be used.
