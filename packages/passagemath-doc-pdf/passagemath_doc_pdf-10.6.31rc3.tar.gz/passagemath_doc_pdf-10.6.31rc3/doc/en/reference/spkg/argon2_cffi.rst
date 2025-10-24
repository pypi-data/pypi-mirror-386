.. _spkg_argon2_cffi:

argon2_cffi: The secure Argon2 password hashing algorithm
=========================================================

Description
-----------

The secure Argon2 password hashing algorithm.

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/argon2-cffi/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_argon2_cffi_bindings`
- :ref:`spkg_flit_core`

Version Information
-------------------

package-version.txt::

    21.3.0

version_requirements.txt::

    argon2-cffi

See https://repology.org/project/argon2-cffi/versions, https://repology.org/project/python:argon2-cffi/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install argon2-cffi

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i argon2_cffi

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install argon2-cffi

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/argon2-cffi

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-argon2-cffi

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-argon2


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
