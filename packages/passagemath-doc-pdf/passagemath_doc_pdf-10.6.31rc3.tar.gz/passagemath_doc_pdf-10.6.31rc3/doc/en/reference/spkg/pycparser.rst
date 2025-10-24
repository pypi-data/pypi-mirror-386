.. _spkg_pycparser:

pycparser: Parser of the C language in Python
=============================================

Description
-----------

development website: https://github.com/eliben/pycparser

PyPI page: https://pypi.org/project/pycparser/

License
-------

BSD

Upstream Contact
----------------

https://github.com/eliben/pycparser


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

    2.22

version_requirements.txt::

    pycparser >=2.20

See https://repology.org/project/pycparser/versions, https://repology.org/project/python:pycparser/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pycparser\>=2.20

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pycparser

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install pycparser

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-pycparser

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/pycparser

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-pycparser

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-pycparser

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-pycparser


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
