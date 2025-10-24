.. _spkg_cluster_pictures:

cluster_pictures: Cluster pictures for local arithmetic data about hyperelliptic curves
=======================================================================================

Description
-----------

This package implements the machinery of cluster pictures of Maistret, Morgan,
Dokchitser and Dokchitser.


License
-------

GPLv2


Upstream Contact
----------------

- https://github.com/alexjbest/cluster-pictures
- https://github.com/passagemath/passagemath-pkg-cluster-pictures


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_combinat`
- :ref:`spkg_sagemath_graphs`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_pari`
- :ref:`spkg_sagemath_plot`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_schemes`
- :ref:`spkg_sagemath_symbolics`

Version Information
-------------------

requirements.txt::

    sage_cluster_pictures @ git+https://github.com/passagemath/passagemath-pkg-cluster-pictures.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install sage_cluster_pictures@git+https://github.com/passagemath/passagemath-pkg-cluster-pictures.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i cluster_pictures


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
