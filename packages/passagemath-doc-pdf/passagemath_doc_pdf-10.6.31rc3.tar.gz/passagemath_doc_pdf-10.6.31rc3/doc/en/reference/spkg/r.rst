.. _spkg_r:

r: A free software environment for statistical computing and graphics
=====================================================================

Description
-----------

R is a language and environment for statistical computing and graphics.
It is a GNU project which is similar to the S language and environment
which was developed at Bell Laboratories (formerly AT&T, now Lucent
Technologies) by John Chambers and colleagues. R can be considered as a
different implementation of S. There are some important differences, but
much code written for S runs unaltered under R.

(taken from http://www.r-project.org/)

License
-------

-  GPL v2 or GPL v3


Upstream Contact
----------------

-  https://www.r-project.org
-  R mailing list, #R in IRC


Special Installation Instructions
---------------------------------

In the Sage distribution, ``r`` is a "dummy" package:
It is here to provide information about equivalent system packages.
R cannot be installed using the Sage distribution.
Please install it manually, either using one of the system package
commands shown here or following the upstream instructions
at https://www.r-project.org


Type
----

optional


Dependencies
------------



Version Information
-------------------

src/pyproject.toml::

    requests >=2.13.0
    rpy2 >=3.3

See https://repology.org/project/r/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   This is a dummy package and cannot be installed using the Sage distribution.

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add R-dev R

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S r

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install r r-essentials r-lattice

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install r-base-dev r-cran-lattice

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install R R-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/R

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-lang/R

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install r

.. tab:: MacPorts:

   No package needed

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr R

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install R-base

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install R


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
