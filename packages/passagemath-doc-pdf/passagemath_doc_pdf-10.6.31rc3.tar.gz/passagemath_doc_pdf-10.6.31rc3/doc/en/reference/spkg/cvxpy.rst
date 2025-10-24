.. _spkg_cvxpy:

cvxpy: Domain-specific language for modeling convex optimization problems in Python
===================================================================================

Description
-----------

Domain-specific language for modeling convex optimization problems in Python

License
-------

Apache License, Version 2.0

Upstream Contact
----------------

https://pypi.org/project/cvxpy/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_clarabel`
- :ref:`spkg_cvxopt`
- :ref:`spkg_ecos_python`
- :ref:`spkg_glpk`
- :ref:`spkg_numpy`
- :ref:`spkg_osqp_python`
- :ref:`spkg_pybind11`
- :ref:`spkg_scipy`
- :ref:`spkg_scs`

Version Information
-------------------

package-version.txt::

    1.6.0

version_requirements.txt::

    cvxpy

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install cvxpy

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i cvxpy

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install cvxpy


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
