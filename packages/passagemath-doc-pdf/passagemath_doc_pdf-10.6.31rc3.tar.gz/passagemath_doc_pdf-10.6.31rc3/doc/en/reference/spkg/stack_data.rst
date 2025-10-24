.. _spkg_stack_data:

stack_data: Extract data from python stack frames and tracebacks for informative displays
=========================================================================================

Description
-----------

Extract data from python stack frames and tracebacks for informative displays

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/stack-data/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_asttokens`
- :ref:`spkg_executing`
- :ref:`spkg_pip`
- :ref:`spkg_pure_eval`

Version Information
-------------------

package-version.txt::

    0.6.3

version_requirements.txt::

    stack-data

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install stack-data

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i stack_data

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install stack_data

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-stack-data

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/stack-data


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
