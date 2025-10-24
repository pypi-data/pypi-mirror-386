.. _spkg_gdb:

gdb: The GNU Project debugger
=============================

Description
-----------

GDB, the GNU Project debugger, allows you to see what is going on
"inside" another program while it executes -- or what another program
was doing at the moment it crashed.

License
-------

GPL v3+


Upstream Contact
----------------

http://www.gnu.org/software/gdb/


Type
----

optional


Dependencies
------------



Version Information
-------------------

See https://repology.org/project/gdb/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   This is a dummy package and cannot be installed using the Sage distribution.

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add gdb

.. tab:: conda-forge:

   No package needed

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install gdb

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install gdb

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install gdb

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install gdb

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install gdb


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
