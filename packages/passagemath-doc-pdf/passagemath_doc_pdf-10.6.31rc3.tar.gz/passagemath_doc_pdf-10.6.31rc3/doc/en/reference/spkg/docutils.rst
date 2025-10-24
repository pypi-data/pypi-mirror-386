.. _spkg_docutils:

docutils: Processing plaintext documentation into useful formats, such as HTML or LaTeX
=======================================================================================

Description
-----------

Docutils is a modular system for processing documentation into useful
formats, such as HTML, XML, and LaTeX. For input Docutils supports
reStructuredText, an easy-to-read, what-you-see-is-what-you-get
plaintext markup syntax.

License
-------

public domain, Python, 2-Clause BSD, GPL 3 (see COPYING.txt)

Upstream Contact
----------------

https://pypi.org/project/docutils/

Home Page: http://docutils.sourceforge.net/


Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    0.21.2

version_requirements.txt::

    docutils >=0.14

See https://repology.org/project/docutils/versions, https://repology.org/project/python:docutils/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install docutils\>=0.14

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i docutils

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install docutils

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-docutils

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/docutils

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install docutils

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-docutils

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-docutils

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-docutils


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
