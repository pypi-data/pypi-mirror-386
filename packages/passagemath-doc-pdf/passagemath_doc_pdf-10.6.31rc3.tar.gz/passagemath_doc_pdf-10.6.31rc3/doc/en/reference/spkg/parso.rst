.. _spkg_parso:

parso: Python Parser
====================

Description
-----------

Parso is a Python parser that supports error recovery and round-trip
parsing for different Python versions (in multiple Python versions).
Parso is also able to list multiple syntax errors in your python file.

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/parso/



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

    0.8.4

version_requirements.txt::

    parso >=0.7.0

See https://repology.org/project/python:parso/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install parso\>=0.7.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i parso

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install parso

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-parso

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/parso

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-parso

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-parso


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
