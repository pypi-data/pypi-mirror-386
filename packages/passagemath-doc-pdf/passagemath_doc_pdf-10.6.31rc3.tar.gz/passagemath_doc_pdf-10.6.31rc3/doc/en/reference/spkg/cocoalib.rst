.. _spkg_cocoalib:

cocoalib: Computations in commutative algebra
=============================================

Description
-----------

CoCoA is a program to compute with numbers and polynomials.

License
-------

-  GPL v3


Upstream Contact
----------------

-  Authors: http://cocoa.dima.unige.it/research/
-  Email: cocoa@dima.unige.it
-  Website: http://cocoa.dima.unige.it/
-  Releases: http://cocoa.dima.unige.it/cocoalib/


Type
----

experimental


Dependencies
------------

- $(MP_LIBRARY)

Version Information
-------------------

package-version.txt::

    0.99564

See https://repology.org/project/cocoalib/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i cocoalib

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install cocoalib cocoalib-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/cocoalib


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
