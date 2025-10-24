.. _spkg_babel:

babel: Internationalization utilities
=====================================

Description
-----------

Internationalization utilities

License
-------

BSD-3-Clause

Upstream Contact
----------------

https://pypi.org/project/Babel/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_pip`
- :ref:`spkg_pytz`

Version Information
-------------------

package-version.txt::

    2.14.0

version_requirements.txt::

    babel >=2.11.0

See https://repology.org/project/python:babel/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install babel\>=2.11.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i babel

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-babel

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install babel

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-babel

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install babel

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/Babel

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-babel

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-Babel

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-Babel


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
