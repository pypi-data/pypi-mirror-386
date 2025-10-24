.. _spkg_pandoc_attributes:

pandoc_attributes: A parser and generator for pandoc block attributes
=====================================================================

Description
-----------

This is a simple parser / emitter for pandoc block attributes, intended
for use with pandocfilters.

License
-------

BSD 2-Clause License


Upstream Contact
----------------

- Author: Aaron O'Leary
- Home page: https://github.com/aaren/pandoc-attributes

Special Update/Build Instructions
---------------------------------

There are no release numbers, hence find the latest commit, download
https://github.com/aaren/pandoc-attributes/archive/${COMMIT}.zip and
rename it pandoc_attributes-${COMMIT:0:8}.zip


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_pandocfilters`

Version Information
-------------------

package-version.txt::

    8bc82f6d

version_requirements.txt::

    pandoc_attributes >=8bc82f6d

See https://repology.org/project/pandoc-attributes/versions, https://repology.org/project/python:pandoc-attributes/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pandoc_attributes\>=8bc82f6d

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pandoc_attributes

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install pandoc-attributes


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
