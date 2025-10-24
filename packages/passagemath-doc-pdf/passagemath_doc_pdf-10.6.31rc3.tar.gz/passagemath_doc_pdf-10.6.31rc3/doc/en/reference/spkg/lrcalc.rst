.. _spkg_lrcalc:

lrcalc: Littlewood-Richardson calculator
========================================

Description
-----------

Littlewood-Richardson Calculator

http://sites.math.rutgers.edu/~asbuch/lrcalc/

License
-------

GNU General Public License V2+


Upstream Contact
----------------

Anders S. Buch (asbuch@math.rutgers.edu)

https://bitbucket.org/asbuch/lrcalc


Type
----

standard


Dependencies
------------



Version Information
-------------------

package-version.txt::

    2.1

src/pyproject.toml::

    lrcalc ~=2.1

See https://repology.org/project/lrcalc/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i lrcalc

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S lrcalc

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install lrcalc

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install liblrcalc-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install lrcalc-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/lrcalc

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge sci-mathematics/lrcalc

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr lrcalc

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install lrcalc-devel


If the system package is installed, ``./configure`` will check if it can be used.
