.. _spkg_jupyterlab_pygments:

jupyterlab_pygments: Pygments theme using JupyterLab CSS variables
==================================================================

Description
-----------

Pygments theme using JupyterLab CSS variables

License
-------

BSD

Upstream Contact
----------------

https://pypi.org/project/jupyterlab-pygments/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_pip`
- :ref:`spkg_pygments`

Version Information
-------------------

package-version.txt::

    0.2.2

version_requirements.txt::

    jupyterlab-pygments

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install jupyterlab-pygments

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i jupyterlab_pygments

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install jupyterlab_pygments

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-jupyterlab_pygments

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/jupyterlab_pygments

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-jupyterlab_pygments


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
