.. _spkg_fpylll:

fpylll: Python interface for FPLLL
==================================

Description
-----------

A Python interface for https://github.com/fplll/fplll (Lattice algorithms using floating-point arithmetic)

License
-------

GPL version 2 or later


Upstream Contact
----------------

https://github.com/fplll/fpylll


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cysignals`
- :ref:`spkg_cython`
- :ref:`spkg_fplll`
- :ref:`spkg_numpy`

Version Information
-------------------

package-version.txt::

    0.6.4

src/pyproject.toml::

    fpylll >=0.5.9

version_requirements.txt::

    fpylll

See https://repology.org/project/fpylll/versions, https://repology.org/project/python:fpylll/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install fpylll\>=0.5.9

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i fpylll

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install fpylll\>=0.5.9

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/fpylll


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
