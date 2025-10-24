.. _spkg_pyyaml:

pyyaml: YAML parser and emitter for Python
==========================================

Description
-----------

YAML parser and emitter for Python

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/PyYAML/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cython`

Version Information
-------------------

package-version.txt::

    6.0.2

version_requirements.txt::

    PyYAML

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install PyYAML

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pyyaml


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
