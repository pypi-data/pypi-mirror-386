.. _spkg_primecount:

primecount: Algorithms for counting primes
==========================================

Description
-----------

primecount is a C++ implementation of several algorithms for counting
primes maintained by Kim Walisch.

Website: https://github.com/kimwalisch/primecount/

License
-------

primecount is licensed BSD 2


Upstream Contact
----------------

-  https://github.com/kimwalisch/primecount/


Type
----

standard


Dependencies
------------

- :ref:`spkg_cmake`
- :ref:`spkg_ninja_build`
- :ref:`spkg_primesieve`

Version Information
-------------------

package-version.txt::

    7.19

See https://repology.org/project/primecount/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i primecount

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S primecount

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install primecount

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libprimecount-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install primecount primecount-devel

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge sci-mathematics/primecount

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install primecount

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install primecount libprimecount-devel

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install primecount-devel


If the system package is installed, ``./configure`` will check if it can be used.
