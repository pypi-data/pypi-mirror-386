.. _spkg_debugpy:

debugpy: Implementation of the Debug Adapter Protocol for Python
================================================================

Description
-----------

Implementation of the Debug Adapter Protocol for Python

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/debugpy/



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

    1.8.1

version_requirements.txt::

    debugpy

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install debugpy

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i debugpy

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install debugpy


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
