.. _spkg_sphinx_copybutton:

sphinx_copybutton: Add a copy button to each of your code cells
===============================================================

Description
-----------

Add a copy button to each of your code cells

License
-------

MIT License

Upstream Contact
----------------

https://pypi.org/project/sphinx-copybutton/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_pip`
- :ref:`spkg_sphinx`

Version Information
-------------------

package-version.txt::

    0.5.2

version_requirements.txt::

    sphinx-copybutton

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install sphinx-copybutton

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sphinx_copybutton

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add py3-sphinx-copybutton

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-sphinx-copybutton

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install sphinx-copybutton

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-sphinx-copybutton

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install textproc/py-sphinx-copybutton

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/sphinx-copybutton

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-sphinx-copybutton


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
