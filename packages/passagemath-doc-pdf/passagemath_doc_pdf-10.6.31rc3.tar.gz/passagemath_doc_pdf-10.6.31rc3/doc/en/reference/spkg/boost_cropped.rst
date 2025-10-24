.. _spkg_boost_cropped:

boost_cropped: Portable C++ libraries (subset needed for Sage)
==============================================================

Description
-----------

Boost provides free peer-reviewed portable C++ source libraries.

We emphasize libraries that work well with the C++ Standard Library.
Boost libraries are intended to be widely useful, and usable across a
broad spectrum of applications. The Boost license encourages both
commercial and non-commercial use.

We aim to establish "existing practice" and provide reference
implementations so that Boost libraries are suitable for eventual
standardization. Ten Boost libraries are already included in the C++
Standards Committee's Library Technical Report (TR1) and will be in the
new C++0x Standard now being finalized. C++0x will also include several
more Boost libraries in addition to those from TR1. More Boost libraries
are proposed for TR2.

License
-------

Boost Software License - see http://www.boost.org/users/license.html


Upstream Contact
----------------

Website: http://www.boost.org/

See mailing list page at http://www.boost.org/community/groups.html


Type
----

standard


Dependencies
------------

- :ref:`spkg_cmake`
- :ref:`spkg_ninja_build`

Version Information
-------------------

package-version.txt::

    1.88.0

See https://repology.org/project/boost/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i boost_cropped

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S boost

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install libboost-devel

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libboost-dev libboost-regex-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install boost-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install devel/boost-libs

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install boost

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install boost

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S -boost

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install boost-devel libboost_regex-devel

.. tab:: pyodide:

   install the following packages: boost-cpp

.. tab:: Slackware:

   .. CODE-BLOCK:: bash

       $ sudo slackpkg install boost

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install boost-devel


If the system package is installed, ``./configure`` will check if it can be used.
