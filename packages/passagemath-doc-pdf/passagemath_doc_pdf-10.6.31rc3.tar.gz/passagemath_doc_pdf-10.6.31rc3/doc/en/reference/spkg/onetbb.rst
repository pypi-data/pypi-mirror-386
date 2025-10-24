.. _spkg_onetbb:

onetbb: oneAPI Threading Building Blocks
========================================

Description
-----------

C++ parallelization library


License
-------

Apache License, Version 2.0


Upstream Contact
----------------

https://github.com/oneapi-src/oneTBB


Type
----

optional


Dependencies
------------

- :ref:`spkg_cmake`
- :ref:`spkg_ninja_build`

Version Information
-------------------

package-version.txt::

    2022.1.0

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i onetbb

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add libtbb-dev

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S intel-oneapi-tbb

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install tbb

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libtbb-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install tbb tbb-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install devel/onetbb

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-cpp/tbb

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install tbb

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install onetbb

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr tbb

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install tbb

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install tbb-devel


If the system package is installed, ``./configure`` will check if it can be used.
