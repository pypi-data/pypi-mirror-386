.. _spkg_sagemath_gap_pkg_agt_data:

=====================================================================================================
sagemath_gap_pkg_agt_data: Computational Group Theory with GAP: agt data
=====================================================================================================


This pip-installable distribution ``passagemath-gap-pkg-agt-data`` is a
distribution of data for use with ``passagemath-gap``.


What is included
----------------

- Wheels on PyPI include the data files of the GAP agt package


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_gap_packages`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.6.31.rc3

version_requirements.txt::

    passagemath-gap-pkg-agt-data == 10.6.31rc3

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-gap-pkg-agt-data==10.6.31rc3

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_gap_pkg_agt_data


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
