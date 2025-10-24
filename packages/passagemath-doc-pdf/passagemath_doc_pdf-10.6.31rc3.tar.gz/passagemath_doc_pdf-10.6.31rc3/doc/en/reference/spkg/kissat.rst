.. _spkg_kissat:

kissat: SAT solver
==================

Description
-----------

From the package README::

    KISSAT is a "keep it simple and clean bare metal SAT solver" written in C.
    It is a port of CaDiCaL back to C with improved data structures, better
    scheduling of inprocessing and optimized algorithms and implementation.

    Coincidentally 'kissat' also means 'cats' in Finnish.

From the website::

    The Kissat SAT solver is a condensed and improved reimplementation of
    CaDiCaL in C.

    Kissat won first place in the main track of the SAT Competition 2020 and
    first place on unsatisfiable instances.

License
-------

MIT license.

Upstream Contact
----------------

Website: https://fmv.jku.at/kissat/


Type
----

optional


Dependencies
------------



Version Information
-------------------

package-version.txt::

    4.0.2

See https://repology.org/project/kissat/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i kissat

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install kissat kissat-devel

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge sci-mathematics/kissat

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr kissat


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
