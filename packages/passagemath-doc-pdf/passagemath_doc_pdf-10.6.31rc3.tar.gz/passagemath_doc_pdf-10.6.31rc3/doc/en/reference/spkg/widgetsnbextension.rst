.. _spkg_widgetsnbextension:

widgetsnbextension: Jupyter interactive widgets for Jupyter Notebook
====================================================================

Description
-----------

Jupyter interactive widgets for Jupyter Notebook

License
-------

BSD 3-Clause License

Upstream Contact
----------------

https://pypi.org/project/widgetsnbextension/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_jupyter_core`
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    4.0.14

version_requirements.txt::

    widgetsnbextension

See https://repology.org/project/python:widgetsnbextension/versions, https://repology.org/project/jupyter-widgetsnbextension/versions, https://repology.org/project/python:jupyter-widgetsnbextension/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install widgetsnbextension

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i widgetsnbextension

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S jupyter-widgetsnbextension

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install widgetsnbextension

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-widgetsnbextension

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install devel/py-widgetsnbextension

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/widgetsnbextension

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-widgetsnbextension

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install jupyter-widgetsnbextension

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-jupyter_widgetsnbextension


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
