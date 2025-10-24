.. _spkg_pynormaliz:

pynormaliz: Python bindings for the normaliz library
====================================================

Description
-----------

The Python module PyNormaliz provides wrappers for normaliz.

License
-------

-  GPL v2 or later


Upstream Contact
----------------

https://pypi.org/project/PyNormaliz/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_normaliz`

Version Information
-------------------

package-version.txt::

    2.23

version_requirements.txt::

    pynormaliz ==2.21

See https://repology.org/project/pynormaliz/versions, https://repology.org/project/python:pynormaliz/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pynormaliz==2.21

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pynormaliz

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-pynormaliz

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install pynormaliz


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
