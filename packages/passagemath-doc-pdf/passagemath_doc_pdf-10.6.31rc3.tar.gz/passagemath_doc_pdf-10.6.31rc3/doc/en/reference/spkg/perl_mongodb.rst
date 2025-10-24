.. _spkg_perl_mongodb:

perl_mongodb: A prerequisite for polymake's PolyDB feature
==========================================================

Description
-----------

This script package represents the Perl package MongoDB, which is needed for
the PolyDB feature of polymake.

License
-------

Various free software licenses


Type
----

optional


Dependencies
------------




Installation commands
---------------------

.. tab:: Sage distribution:

   This is a dummy package and cannot be installed using the Sage distribution.

.. tab:: cpan:

   .. CODE-BLOCK:: bash

       $ cpan -i MongoDB

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libmongodb-perl

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install perl-MongoDB

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install databases/p5-MongoDB

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-perl/MongoDB


If the system package is installed, ``./configure`` will check if it can be used.
