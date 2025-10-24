.. _spkg_ore_algebra:

ore_algebra: Ore algebra
========================

Description
-----------

A Sage implementation of Ore algebras, Ore polynomials, and differentially
finite functions.

Main features for the most common algebras include basic arithmetic and
actions; gcrd and lclm; D-finite closure properties; creative telescoping;
natural transformations between related algebras; guessing; desingularization;
solvers for polynomials, rational functions and (generalized) power series.
Univariate differential operators also support the numerical computation of
analytic solutions with rigorous error bounds and related features.

License
-------

-  GPL-2.0+


Upstream Contact
----------------

- Website: https://github.com/mkauers/ore_algebra/
- Sage accounts: mkauers, mmezzarobba



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- $(SAGERUNTIME)

Version Information
-------------------

requirements.txt::

    ore_algebra @ git+https://github.com/mkauers/ore_algebra

See https://repology.org/project/ore-algebra/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install ore_algebra@git+https://github.com/mkauers/ore_algebra

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i ore_algebra


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
