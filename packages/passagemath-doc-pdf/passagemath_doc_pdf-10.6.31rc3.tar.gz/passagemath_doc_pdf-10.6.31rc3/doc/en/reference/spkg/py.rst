.. _spkg_py:

py: Library with cross-python path, ini-parsing, io, code, log facilities
=========================================================================

Description
-----------

Library with cross-python path, ini-parsing, io, code, log facilities

License
-------

MIT license

Upstream Contact
----------------

https://pypi.org/project/py/



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

    1.11.0

version_requirements.txt::

    py

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install py

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i py

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-py

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install py

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-py

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-py

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/py

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-py

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-py


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
