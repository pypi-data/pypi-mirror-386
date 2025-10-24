.. _spkg_beniget:

beniget: Extract semantic information about static Python code
==============================================================

Description
-----------

Extract semantic information about static Python code

License
-------

BSD 3-Clause

Upstream Contact
----------------

https://pypi.org/project/beniget/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_gast`

Version Information
-------------------

package-version.txt::

    0.4.2.post1

version_requirements.txt::

    beniget

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install beniget

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i beniget

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install beniget

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-beniget

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/beniget

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-beniget


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
