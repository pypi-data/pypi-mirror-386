.. _spkg_m4ri:

m4ri: fast arithmetic with dense matrices over GF(2)
====================================================

Description
-----------

M4RI: Library for matrix multiplication, reduction and inversion over
GF(2). (See also m4ri/README for a brief overview.)

License
-------

-  GNU General Public License Version 2 or later (see src/COPYING)


Upstream Contact
----------------

-  Authors: Martin Albrecht et al.
-  Email: <m4ri-devel@googlegroups.com>
-  Website: https://bitbucket.org/malb/m4ri


Type
----

standard


Dependencies
------------

- :ref:`spkg_libpng`

Version Information
-------------------

package-version.txt::

    20250128

See https://repology.org/project/libm4ri/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i m4ri

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S m4ri

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install m4ri

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libm4ri-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install m4ri-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/m4ri

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge sci-libs/m4ri\[png\]

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr m4ri

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install pkgconfig\(m4ri\)

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install m4ri-devel


If the system package is installed, ``./configure`` will check if it can be used.
