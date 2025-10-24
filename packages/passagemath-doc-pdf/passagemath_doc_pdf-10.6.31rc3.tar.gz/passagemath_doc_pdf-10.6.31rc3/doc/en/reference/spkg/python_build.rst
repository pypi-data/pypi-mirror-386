.. _spkg_python_build:

python_build: A simple, correct PEP517 package builder
======================================================

Description
-----------

``build`` is a simple, correct PEP517 package builder

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/build/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_importlib_metadata`
- :ref:`spkg_packaging`
- :ref:`spkg_pip`
- :ref:`spkg_pyproject_hooks`
- :ref:`spkg_tomli`

Version Information
-------------------

package-version.txt::

    1.2.1

version_requirements.txt::

    build

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install build

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i python_build

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install python-build


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
