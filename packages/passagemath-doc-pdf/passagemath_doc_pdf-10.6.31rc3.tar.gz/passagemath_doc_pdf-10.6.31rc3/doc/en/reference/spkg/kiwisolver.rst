.. _spkg_kiwisolver:

kiwisolver: Fast implementation of the Cassowary constraint solver
==================================================================

Description
-----------

From https://pypi.org/project/kiwisolver/

A fast implementation of the Cassowary constraint solver

Kiwi is an efficient C++ implementation of the Cassowary constraint
solving algorithm. Kiwi is an implementation of the algorithm based on
the seminal Cassowary paper. It is not a refactoring of the original C++
solver. Kiwi has been designed from the ground up to be lightweight and
fast. Kiwi ranges from 10x to 500x faster than the original Cassowary
solver with typical use cases gaining a 40x improvement. Memory savings
are consistently > 5x.

In addition to the C++ solver, Kiwi ships with hand-rolled Python
bindings.

License
-------

Modified BSD License


Upstream Contact
----------------

https://github.com/nucleic/kiwi


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cppy`

Version Information
-------------------

package-version.txt::

    1.4.9

version_requirements.txt::

    kiwisolver >=1.4.8

See https://repology.org/project/python:kiwisolver/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install kiwisolver\>=1.4.8

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i kiwisolver

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install kiwisolver

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-kiwisolver

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/kiwisolver

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-kiwisolver

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-kiwisolver


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
