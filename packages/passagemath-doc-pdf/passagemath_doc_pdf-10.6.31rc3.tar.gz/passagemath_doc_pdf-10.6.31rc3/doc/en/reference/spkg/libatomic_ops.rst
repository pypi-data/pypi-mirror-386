.. _spkg_libatomic_ops:

libatomic_ops: Access hardware-provided atomic memory update operations
=======================================================================

Description
-----------

This package provides semi-portable access to hardware-provided
atomic memory update operations on a number of architectures.


License
-------

- MIT (core library) + GPL 2.0+ (gpl extension library)


Upstream Contact
----------------

https://github.com/ivmai/libatomic_ops/


Special Update/Build Instructions
---------------------------------

None.


Type
----

standard


Dependencies
------------



Version Information
-------------------

package-version.txt::

    7.8.2

See https://repology.org/project/libatomic-ops/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i libatomic_ops

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add libatomic_ops-dev

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S libatomic_ops

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install libatomic_ops

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libatomic-ops-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install libatomic_ops libatomic_ops-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install devel/libatomic_ops

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-libs/libatomic_ops

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install libatomic_ops

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install libatomic_ops

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S -libatomic_ops

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install pkgconfig\(atomic_ops\)

.. tab:: Slackware:

   .. CODE-BLOCK:: bash

       $ sudo slackpkg install libatomic_ops

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install libatomic_ops-devel


If the system package is installed, ``./configure`` will check if it can be used.
