.. _spkg_gc:

gc: The Boehm-Demers-Weiser conservative garbage collector
==========================================================

Description
-----------

The Boehm-Demers-Weiser conservative garbage collector.


License
-------

-  MIT-style (https://github.com/ivmai/bdwgc/blob/master/LICENSE)


Upstream Contact
----------------

-  Ivan Maidanski

Webpage:
-  https://github.com/ivmai/bdwgc/
-  https://www.hboehm.info/gc/


Special Update/Build Instructions
---------------------------------

None.


Type
----

standard


Dependencies
------------

- :ref:`spkg_libatomic_ops`

Version Information
-------------------

package-version.txt::

    8.2.8

See https://repology.org/project/boehm-gc/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i gc

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add gc-dev

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S gc

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install bdw-gc

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libgc-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install gc gc-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install devel/boehm-gc devel/boehm-gc-threaded

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-libs/boehm-gc

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install bdw-gc

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install boehmgc

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S -gc

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install pkgconfig\(bdw-gc\)

.. tab:: Slackware:

   .. CODE-BLOCK:: bash

       $ sudo slackpkg install gc

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install gc-devel


If the system package is installed, ``./configure`` will check if it can be used.
