.. _spkg_furo:

furo: A clean customizable Sphinx documentation theme
=====================================================

Description
-----------

A clean customizable Sphinx documentation theme.

License
-------

Copyright (c) 2020 Pradyun Gedam <mail@pradyunsg.me>  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Upstream Contact
----------------

https://pypi.org/project/furo/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_beautifulsoup4`
- :ref:`spkg_pip`
- :ref:`spkg_pygments`
- :ref:`spkg_sphinx`
- :ref:`spkg_sphinx_basic_ng`

Version Information
-------------------

package-version.txt::

    2024.8.6

version_requirements.txt::

    furo >= 2024.7.18

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install furo\>=2024.7.18

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i furo

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-sphinx-furo

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install furo

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install furo

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-furo

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install textproc/py-furo

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/furo


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
