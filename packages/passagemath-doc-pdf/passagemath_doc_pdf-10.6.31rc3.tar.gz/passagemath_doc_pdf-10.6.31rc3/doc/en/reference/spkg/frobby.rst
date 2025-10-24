.. _spkg_frobby:

frobby: Computations on monomial ideals
=======================================

Description
-----------

The software package Frobby provides a number of computations on
monomial ideals. The current main feature is the socle of a monomial
ideal, which is largely equivalent to computing the maximal standard
monomials, the Alexander dual or the irreducible decomposition.

Operations on monomial ideals are much faster than algorithms designed
for ideals in general, which is what makes a specialized library for
these operations on monomial ideals useful.

License
-------

-  GPL version 2.0 or later


Upstream Contact
----------------

- http://www.broune.com/frobby/  (defunct)

- https://github.com/Macaulay2/frobby


Type
----

optional


Dependencies
------------

- $(MP_LIBRARY)
- :ref:`spkg_cmake`

Version Information
-------------------

package-version.txt::

    0.9.5.p0

See https://repology.org/project/frobby/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i frobby

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install frobby libfrobby libfrobby-devel


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
