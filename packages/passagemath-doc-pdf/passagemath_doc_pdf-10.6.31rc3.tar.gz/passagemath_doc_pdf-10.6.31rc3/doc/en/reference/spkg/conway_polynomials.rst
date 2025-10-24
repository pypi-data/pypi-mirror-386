.. _spkg_conway_polynomials:

conway_polynomials: Python interface to Frank Lübeck's Conway polynomial database
=================================================================================

Description
-----------

This python module evolved from the old SageMath *conway_polynomials*
package once hosted at,

  http://files.sagemath.org/spkg/upstream/conway_polynomials/

It's still maintained by Sage developers, but having a pip-installable
interface to the data will make it easier to install SageMath via pip
or another package manager.


License
-------

GPL version 3 or later


Upstream Contact
----------------

https://github.com/sagemath/conway-polynomials


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

    0.10

src/pyproject.toml::

    conway-polynomials >=0.8

version_requirements.txt::

    conway-polynomials

See https://repology.org/project/sagemath-conway-polynomials/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install conway-polynomials\>=0.8

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i conway_polynomials

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S sage-data-conway_polynomials

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install conway-polynomials

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/conway-polynomials


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
