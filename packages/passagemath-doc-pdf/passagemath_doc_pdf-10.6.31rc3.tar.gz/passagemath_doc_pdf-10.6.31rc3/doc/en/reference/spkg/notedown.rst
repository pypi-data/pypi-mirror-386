.. _spkg_notedown:

notedown: Create IPython notebooks from markdown
================================================

Description
-----------

Notedown is a simple tool to create IPython notebooks from markdown.

License
-------

BSD 2-Clause License


Upstream Contact
----------------

Author: Aaron O'Leary Home page: https://github.com/aaren/notedown



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_nbconvert`
- :ref:`spkg_nbformat`
- :ref:`spkg_pandoc_attributes`
- :ref:`spkg_six`

Version Information
-------------------

package-version.txt::

    1.5.1

version_requirements.txt::

    notedown >=1.5.1

See https://repology.org/project/python:notedown/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install notedown\>=1.5.1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i notedown

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install notedown


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
