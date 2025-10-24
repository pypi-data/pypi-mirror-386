.. _spkg_matplotlib_inline:

matplotlib_inline: Inline Matplotlib backend for Jupyter
========================================================

Description
-----------

Inline Matplotlib backend for Jupyter

License
-------

BSD 3-Clause

Upstream Contact
----------------

https://pypi.org/project/matplotlib-inline/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_pip`
- :ref:`spkg_traitlets`

Version Information
-------------------

package-version.txt::

    0.1.7

version_requirements.txt::

    matplotlib-inline

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install matplotlib-inline

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i matplotlib_inline

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install matplotlib-inline

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-matplotlib-inline

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/matplotlib-inline

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-matplotlib-inline


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
