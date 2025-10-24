.. _spkg_glpk:

glpk: GNU Linear Programming Kit
================================

Description
-----------

The GLPK (GNU Linear Programming Kit) package is intended for solving
large-scale linear programming (LP), mixed integer programming (MIP),
and other related problems. It is a set of routines written in ANSI C
and organized in the form of a callable library.

GLPK supports the GNU MathProg modelling language, which is a subset of
the AMPL language.

The GLPK package includes the following main components:

-  primal and dual simplex methods
-  primal-dual interior-point method
-  branch-and-cut method
-  translator for GNU MathProg
-  application program interface (API)
-  stand-alone LP/MIP solver

License
-------

The GLPK package is GPL version 3.


Upstream Contact
----------------

GLPK is currently being maintained by:

-  Andrew Makhorin (mao@gnu.org, mao@mai2.rcnet.ru)

http://www.gnu.org/software/glpk/#maintainer

Special Update/Build Instructions
---------------------------------

-  ``configure`` doesn't support specifying the location of the GMP
   library to use; only ``--with-gmp[=yes]`` or ``--with-gmp=no``
   are valid options. (So we \*have to\* add Sage's include and
   library directories to ``CPPFLAGS`` and ``LDFLAGS``, respectively.)

-  Do we need the ``--disable-static``? The stand-alone solver presumably
   runs faster when built with a static library; also other
   (stand-alone)
   programs using it would.
   (Instead, we should perhaps use ``--enable-static --enable-shared``
   to
   go safe.)


Type
----

standard


Dependencies
------------

- $(MP_LIBRARY)
- :ref:`spkg_zlib`

Version Information
-------------------

package-version.txt::

    5.0.p1

See https://repology.org/project/glpk/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i glpk

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add glpk-dev

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S glpk

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install glpk

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install glpk-utils libglpk-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install glpk glpk-devel glpk-utils

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/glpk

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge sci-mathematics/glpk

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install glpk

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install glpk

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S -glpk

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr glpk

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install glpk glpk-devel

.. tab:: pyodide:

   install the following packages: glpk

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install glpk-devel


If the system package is installed, ``./configure`` will check if it can be used.
