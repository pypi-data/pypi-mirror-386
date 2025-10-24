.. _spkg_jupyter_sphinx:

jupyter_sphinx: Jupyter Sphinx Extension
========================================

Description
-----------

Jupyter Sphinx Extension

License
-------

BSD

Upstream Contact
----------------

https://pypi.org/project/jupyter-sphinx/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_ipython`
- :ref:`spkg_ipywidgets`
- :ref:`spkg_nbconvert`
- :ref:`spkg_nbformat`
- :ref:`spkg_sphinx`

Version Information
-------------------

package-version.txt::

    0.5.3.p0

version_requirements.txt::

    jupyter-sphinx

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install jupyter-sphinx

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i jupyter_sphinx

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-jupyter-sphinx

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install jupyter_sphinx

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-jupyter-sphinx

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install textproc/py-jupyter_sphinx

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-jupyter_sphinx

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python-jupyter-sphinx


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
