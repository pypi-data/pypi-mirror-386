.. _spkg_gnulib:

gnulib: Modules imported from Gnulib
====================================

This script package represents the modules imported into the Sage source tree from Gnulib.

Upstream Contact
----------------

https://www.gnu.org/software/gnulib/


Type
----

standard


Dependencies
------------



Version Information
-------------------

package-version.txt::

    f9b39c4e337f1dc0dd07c4f3985c476fb875d799

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i gnulib


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
