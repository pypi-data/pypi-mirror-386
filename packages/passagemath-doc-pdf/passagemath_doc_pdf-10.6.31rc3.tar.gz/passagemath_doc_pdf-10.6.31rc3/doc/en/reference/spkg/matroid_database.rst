.. _spkg_matroid_database:

matroid_database: Python interface to matroid database
======================================================

Description
-----------

Python interface to matroid database.

This database was retrieved from
<https://www-imai.is.s.u-tokyo.ac.jp/~ymatsu/matroid/index.html>
(Yoshitake Matsumoto, Database of Matroids, 2012; accessed: 2023.12.02).


License
-------

GPL version 3 or later


Upstream Contact
----------------

https://pypi.org/project/matroid-database

https://github.com/gmou3/matroid-database


Type
----

optional


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    0.3

version_requirements.txt::

    matroid-database

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install matroid-database

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i matroid_database


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
