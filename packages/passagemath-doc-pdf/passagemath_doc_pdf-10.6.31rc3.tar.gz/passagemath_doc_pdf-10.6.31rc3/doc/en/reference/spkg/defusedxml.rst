.. _spkg_defusedxml:

defusedxml: Addresses vulnerabilities of XML parsers and XML libraries
======================================================================

Description
-----------

defusedxml addresses vulnerabilities of XML parsers and XML libraries.

It became a dependency of nbconvert starting with nbconvert 5.4.

License
-------

Python Software Foundation License (PSFL)


Upstream Contact
----------------

https://pypi.org/project/defusedxml/

Special Update/Build Instructions
---------------------------------

None.


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)

Version Information
-------------------

package-version.txt::

    0.7.1

version_requirements.txt::

    defusedxml >=0.6.0

See https://repology.org/project/python:defusedxml/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install defusedxml\>=0.6.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i defusedxml

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install defusedxml

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-defusedxml

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/defusedxml

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-defusedxml

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-defusedxml


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
