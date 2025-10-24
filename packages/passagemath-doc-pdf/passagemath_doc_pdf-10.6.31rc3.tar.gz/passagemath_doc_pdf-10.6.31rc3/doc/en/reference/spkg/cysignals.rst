.. _spkg_cysignals:

cysignals: Interrupt and signal handling for Cython
===================================================

Description
-----------

Interrupt and signal handling for Cython

License
-------

LGPL version 3 or later


Upstream Contact
----------------

https://github.com/sagemath/cysignals



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cython`
- :ref:`spkg_meson_python`

Version Information
-------------------

package-version.txt::

    34fcd3d594037ae61568f9602dacf9393c2a7fed

src/pyproject.toml::

    cysignals <1.12.4; sys_platform == 'win32'
    cysignals >=1.11.2, != 1.12.0

version_requirements.txt::

    cysignals

See https://repology.org/project/cysignals/versions, https://repology.org/project/python:cysignals/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install cysignals\<1.12.4\;sys_platform==\"win32\" cysignals\>=1.11.2\,\!=1.12.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i cysignals

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install cysignals

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/cysignals


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
