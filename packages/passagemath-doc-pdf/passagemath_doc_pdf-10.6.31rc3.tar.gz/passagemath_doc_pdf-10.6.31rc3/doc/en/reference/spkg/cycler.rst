.. _spkg_cycler:

cycler: Composable cycles
=========================

Description
-----------

Cycler is a small break-off of matplotlib to deal with "composable
cycles". It is a required dependency of matplotlib 1.5.0.

License
-------

BSD


Upstream Contact
----------------

cycler is developed on github: https://github.com/matplotlib/cycler

A more informative webpage about cycler, its motivation and usage is at
http://tacaswell.github.io/cycler/


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)

Version Information
-------------------

package-version.txt::

    0.12.1

version_requirements.txt::

    cycler >=0.12.1

See https://repology.org/project/cycler/versions, https://repology.org/project/python:cycler/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install cycler\>=0.12.1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i cycler

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-cycler

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install cycler

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-cycler

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-cycler

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install devel/py-cycler

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/cycler

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-cycler

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-Cycler

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-cycler


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
