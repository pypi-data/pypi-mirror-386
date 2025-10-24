.. _spkg_ply:

ply: Python Lex & Yacc
======================

Description
-----------

Python Lex & Yacc

License
-------

BSD

Upstream Contact
----------------

https://pypi.org/project/ply/



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

    3.11

version_requirements.txt::

    ply

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install ply

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i ply

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install ply

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/ply

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-ply


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
