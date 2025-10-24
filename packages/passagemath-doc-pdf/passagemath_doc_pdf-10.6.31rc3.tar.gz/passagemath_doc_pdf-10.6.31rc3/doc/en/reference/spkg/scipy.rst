.. _spkg_scipy:

scipy: Scientific tools for Python
==================================

Description
-----------

SciPy (pronounced "Sigh Pie") is open-source software for mathematics,
science, and engineering. The SciPy library depends on NumPy, which
provides convenient and fast N-dimensional array manipulation. The SciPy
library is built to work with NumPy arrays, and provides many
user-friendly and efficient numerical routines such as routines for
numerical integration and optimization. Together, they run on all
popular operating systems, are quick to install, and are free of charge.
NumPy and SciPy are easy to use, but powerful enough to be depended upon
by some of the world's leading scientists and engineers.

License
-------

SciPy's license is free for both commercial and non-commercial use,
under the BSD terms. See http://www.scipy.org/License_Compatibility


Upstream Contact
----------------

   https://www.scipy.org/

Dependencies
------------

-  Python, which in Sage has numerous dependencies
-  Numpy
-  Fortran
-  GNU patch


Special Update/Build Instructions
---------------------------------

-  None.


Type
----

standard


Dependencies
------------

- $(BLAS)
- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cython`
- :ref:`spkg_gfortran`
- :ref:`spkg_meson_python`
- :ref:`spkg_numpy`
- :ref:`spkg_pybind11`
- :ref:`spkg_pythran`

Version Information
-------------------

package-version.txt::

    1.15.3

src/pyproject.toml::

    scipy >=1.5

version_requirements.txt::

    scipy >=1.12

See https://repology.org/project/python:scipy/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install scipy\>=1.5

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i scipy

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-scipy

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install scipy\>=1.12

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-scipy

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-scipy

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/scipy

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install scipy

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-scipy

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-scipy

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-scipy


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
