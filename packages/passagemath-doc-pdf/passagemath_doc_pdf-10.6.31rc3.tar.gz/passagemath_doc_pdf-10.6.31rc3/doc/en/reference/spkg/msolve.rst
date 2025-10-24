.. _spkg_msolve:

msolve: Multivariate polynomial system solver
=============================================

Description
-----------

Open source C library implementing computer algebra algorithms for solving
polynomial systems (with rational coefficients or coefficients in a prime field).

License
-------

GPL v2+

Upstream Contact
----------------

https://github.com/algebraic-solving/msolve


Type
----

optional


Dependencies
------------

- $(MP_LIBRARY)
- :ref:`spkg__bootstrap`
- :ref:`spkg_flint`
- :ref:`spkg_mpfr`

Version Information
-------------------

package-version.txt::

    0.9.2

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i msolve


If the system package is installed, ``./configure`` will check if it can be used.
