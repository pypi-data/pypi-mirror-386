.. _spkg_pyscipopt:

pyscipopt: Python interface and modeling environment for SCIP
=============================================================

Description
-----------

Python interface and modeling environment for SCIP

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/PySCIPOpt/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cython`
- :ref:`spkg_numpy`
- :ref:`spkg_scip`

Version Information
-------------------

package-version.txt::

    5.5.0

version_requirements.txt::

    PySCIPOpt

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install PySCIPOpt

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pyscipopt

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install pyscipopt

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/py-PySCIPOpt


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
