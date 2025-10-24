.. _spkg_cppy:

cppy: C++ headers for C extension development
===========================================================================

Description
-----------

From: https://pypi.org/project/cppy/

A small C++ header library which makes it easier to write Python extension
modules. The primary feature is a PyObject smart pointer which automatically
handles reference counting and provides convenience methods for performing
common object operations.

License
-------

Modified BSD 3-Clause-License

Upstream Contact
----------------

https://github.com/nucleic/cppy


Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    1.3.1

version_requirements.txt::

    cppy >=1.2.0

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install cppy\>=1.2.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i cppy

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install cppy

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-cppy

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/cppy


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
