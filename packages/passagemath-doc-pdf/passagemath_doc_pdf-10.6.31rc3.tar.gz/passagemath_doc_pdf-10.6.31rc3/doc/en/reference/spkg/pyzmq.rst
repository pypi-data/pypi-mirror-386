.. _spkg_pyzmq:

pyzmq: Python bindings for the zeromq networking library
========================================================

Description
-----------

Python bindings for the zeromq networking library.

License
-------

LGPLv3+


Upstream Contact
----------------

http://www.zeromq.org

Special Update/Build Instructions
---------------------------------

None.


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cmake`
- :ref:`spkg_cython`
- :ref:`spkg_ninja_build`
- :ref:`spkg_packaging`
- :ref:`spkg_scikit_build_core`
- :ref:`spkg_zeromq`

Version Information
-------------------

package-version.txt::

    26.4.0

version_requirements.txt::

    pyzmq >=19.0.2

See https://repology.org/project/pyzmq/versions, https://repology.org/project/python:pyzmq/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pyzmq\>=19.0.2

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pyzmq

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-pyzmq

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install pyzmq

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-pyzmq

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/pyzmq

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-pyzmq

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-pyzmq


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
