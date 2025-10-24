.. _spkg_pythran:

pythran: Ahead of Time compiler for numeric kernels
===================================================

Description
-----------

Ahead of Time compiler for numeric kernels

License
-------

BSD 3-Clause

Upstream Contact
----------------

https://pypi.org/project/pythran/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_beniget`
- :ref:`spkg_gast`
- :ref:`spkg_pip`
- :ref:`spkg_ply`

Version Information
-------------------

package-version.txt::

    0.17.0

version_requirements.txt::

    pythran>=0.14.0,<0.18.0

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pythran\>=0.14.0\,\<0.18.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pythran

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install pythran\>=0.14.0\,\<0.18

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install pythran

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/pythran

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install pythran


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
