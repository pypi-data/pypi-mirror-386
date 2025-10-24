.. _spkg_scip:

scip: Mixed integer programming solver
======================================

Description
-----------

SCIP is currently one of the fastest open source mixed integer
programming (MIP) solvers. It is also a framework for constraint integer
programming and branch-cut-and-price. It allows total control of the
solution process and the access of detailed information down to the guts
of the solver.

License
-------

Apache 2.0


Upstream Contact
----------------

https://scipopt.org/#scipoptsuite


Dependencies
------------

scip brings its own patched version of the bliss library.
This will conflict with the optional package bliss.


Type
----

optional


Dependencies
------------

- $(MP_LIBRARY)
- :ref:`spkg_bliss`
- :ref:`spkg_cmake`
- :ref:`spkg_ninja_build`
- :ref:`spkg_papilo`
- :ref:`spkg_readline`
- :ref:`spkg_soplex`
- :ref:`spkg_zlib`

Version Information
-------------------

package-version.txt::

    9.2.3

src/pyproject.toml::

    scipy >=1.5

See https://repology.org/project/scipoptsuite/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i scip

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install scip

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install scip


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
