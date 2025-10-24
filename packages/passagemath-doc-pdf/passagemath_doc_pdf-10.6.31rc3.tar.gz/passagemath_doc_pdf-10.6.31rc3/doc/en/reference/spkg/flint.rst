.. _spkg_flint:

flint: Fast Library for Number Theory
=====================================

Description
-----------

FLINT is a C library for doing number theory, maintained by
Fredrik Johansson.

Website: http://www.flintlib.org

License
-------

FLINT is licensed GPL v2+.


Upstream Contact
----------------

-  flint-devel Gougle Group
   (http://groups.google.co.uk/group/flint-devel)
-  Fredrik Johansson


Type
----

standard


Dependencies
------------

- $(MP_LIBRARY)
- :ref:`spkg_cmake`
- :ref:`spkg_mpfr`
- :ref:`spkg_ninja_build`

Version Information
-------------------

package-version.txt::

    3.3.1

See https://repology.org/project/flint/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i flint

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add flint-dev

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install libflint\<3.3.0a0

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libflint-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install flint flint-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/flint2

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge sci-mathematics/flint\[ntl\]

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install flint

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install flint

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S -flint

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr flint

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install flint-devel

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install flintlib-devel


If the system package is installed, ``./configure`` will check if it can be used.
