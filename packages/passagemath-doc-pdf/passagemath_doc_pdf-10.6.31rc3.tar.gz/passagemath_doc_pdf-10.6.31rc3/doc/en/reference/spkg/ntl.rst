.. _spkg_ntl:

ntl: A library for doing number theory
======================================

Description
-----------

NTL is a high-performance, portable C++ library providing data
structures and algorithms for manipulating signed, arbitrary length
integers, and for vectors, matrices, and polynomials over the integers
and over finite fields.

Website: https://libntl.org/

License
-------

-  GNU LGPLv2.1+


Upstream Contact
----------------

-  Victor Shoup - for contact info see http://www.shoup.net/


Type
----

standard


Dependencies
------------

- $(MP_LIBRARY)
- :ref:`spkg_gf2x`

Version Information
-------------------

package-version.txt::

    11.5.1

See https://repology.org/project/ntl/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i ntl

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install ntl

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libntl-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install ntl-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/ntl

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-libs/ntl

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install ntl

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install ntl

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr ntl

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install ntl-devel

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install ntl-devel


If the system package is installed, ``./configure`` will check if it can be used.
