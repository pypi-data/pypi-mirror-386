.. _spkg_isoduration:

isoduration: Operations with ISO 8601 durations
===============================================

Description
-----------

Operations with ISO 8601 durations

License
-------

Upstream Contact
----------------

https://pypi.org/project/isoduration/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_arrow`
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    20.11.0

version_requirements.txt::

    isoduration

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install isoduration

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i isoduration


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
