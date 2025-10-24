.. _spkg_python_igraph:

python_igraph: Python bindings for igraph
=========================================

Description
-----------

igraph is a library for creating and manipulating graphs. It is intended
to be as powerful (ie. fast) as possible to enable the analysis of large
graphs.

License
-------

GPL version 2


Upstream Contact
----------------

http://igraph.org/python/

Special Update/Build Instructions
---------------------------------


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_igraph`
- :ref:`spkg_texttable`

Version Information
-------------------

package-version.txt::

    0.11.8

version_requirements.txt::

    igraph

See https://repology.org/project/python:igraph/versions, https://repology.org/project/python:python-igraph/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install igraph

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i python_igraph

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-igraph

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install python-igraph

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-igraph

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python-igraph python3-igraph-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/py-igraph

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-igraph


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
