.. _spkg_openblas:

openblas: An optimized implementation of BLAS (Basic Linear Algebra Subprograms)
================================================================================

Description
-----------

OpenBLAS is an optimized open library implementing the Basic Linear Algebra Subprograms
(BLAS) specification.

It is based on GotoBLAS2 1.13 BSD version.

License
-------

3-clause BSD license


SPKG Repository
---------------

https://www.openblas.net

GitHub page: https://github.com/xianyi/OpenBLAS

Releases: https://github.com/xianyi/OpenBLAS/releases


Upstream Contact
----------------

-  OpenBLAS users mailing list:

   https://groups.google.com/forum/#!forum/openblas-users

-  OpenBLAS developers mailing list:

   https://groups.google.com/forum/#!forum/openblas-dev


Type
----

standard


Dependencies
------------

- :ref:`spkg_gfortran`

Version Information
-------------------

package-version.txt::

    0.3.29

See https://repology.org/project/openblas/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i openblas

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add openblas-dev

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S openblas lapack cblas

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install openblas blas=2.\*=openblas

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libopenblas-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install openblas-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/openblas

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge sci-libs/openblas

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install openblas

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install OpenBLAS-devel

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S -openblas

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr blas lapack

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install openblas-devel

.. tab:: pyodide:

   install the following packages: openblas

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install openblas-devel


If the system package is installed, ``./configure`` will check if it can be used.
