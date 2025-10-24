.. _spkg_sagenb_export:

sagenb_export: Convert legacy SageNB notebooks to Jupyter notebooks and other formats
=====================================================================================

Description
-----------

This is a tool to convert SageNB notebooks to other formats, in
particular IPython/Jupyter notebooks.

It includes a Jupyter notebook extension to provide a UI for the import
of SageNB notebooks.

Upstream Contact
----------------

https://github.com/vbraun/ExportSageNB


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_ipython`
- :ref:`spkg_nbconvert`
- :ref:`spkg_notebook`
- :ref:`spkg_six`

Version Information
-------------------

package-version.txt::

    3.3

version_requirements.txt::

    git+https://github.com/vbraun/ExportSageNB.git

See https://repology.org/project/sagenb-export/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install git+https://github.com/vbraun/ExportSageNB.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagenb_export


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
