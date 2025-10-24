.. _spkg_zeromq:

zeromq: A modern networking library
===================================

Description
-----------

A modern networking library. Also known as 0mq or zmq. The same API is
provided by http://www.crossroads.io, though we currently use the
http://www.zeromq.org implementation.

License
-------

LGPLv3+


Upstream Contact
----------------

http://www.zeromq.org

Dependencies
------------

A working compiler.


Special Update/Build Instructions
---------------------------------

N/A


Type
----

standard


Dependencies
------------



Version Information
-------------------

package-version.txt::

    4.3.5

See https://repology.org/project/zeromq/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i zeromq

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add zeromq-dev

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S zeromq

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install zeromq

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libzmq3-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install zeromq zeromq-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install net/libzmq4

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge net-libs/zeromq

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install zeromq

.. tab:: MacPorts:

   No package needed

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S -zeromq

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install pkgconfig\(libzmq\)

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install zeromq-devel


If the system package is installed, ``./configure`` will check if it can be used.
