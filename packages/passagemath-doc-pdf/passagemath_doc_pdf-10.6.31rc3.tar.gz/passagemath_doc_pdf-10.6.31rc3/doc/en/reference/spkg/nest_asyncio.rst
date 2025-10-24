.. _spkg_nest_asyncio:

nest_asyncio: Patch asyncio to allow nested event loops
=======================================================

Description
-----------

Patch asyncio to allow nested event loops

License
-------

BSD

Upstream Contact
----------------

https://pypi.org/project/nest-asyncio/



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

    1.6.0

version_requirements.txt::

    nest-asyncio

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install nest-asyncio

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i nest_asyncio

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install nest-asyncio

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-nest-asyncio

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/nest_asyncio

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-nest_asyncio


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
