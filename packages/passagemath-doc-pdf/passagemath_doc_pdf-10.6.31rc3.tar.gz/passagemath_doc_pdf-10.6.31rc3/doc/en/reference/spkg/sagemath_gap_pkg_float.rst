.. _spkg_sagemath_gap_pkg_float:

=================================================================================================
sagemath_gap_pkg_float: Computational Group Theory with GAP: float package
=================================================================================================


This pip-installable distribution ``passagemath-gap-pkg-float`` is a
distribution of the GAP package ``float`` for use with ``passagemath-gap``.


What is included
----------------

- Wheels on PyPI include the GAP package ``float``


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cython`
- :ref:`spkg_gap_packages`
- :ref:`spkg_pkgconfig`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.6.31.rc3

version_requirements.txt::

    passagemath-gap-pkg-float == 10.6.31rc3

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-gap-pkg-float==10.6.31rc3

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_gap_pkg_float


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
