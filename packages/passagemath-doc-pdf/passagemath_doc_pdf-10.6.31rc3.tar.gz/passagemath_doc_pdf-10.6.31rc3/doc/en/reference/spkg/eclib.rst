.. _spkg_eclib:

eclib: Enumerating and computing with elliptic curves defined over the rational numbers
=======================================================================================

Description
-----------

John Cremona's programs for enumerating and computing with elliptic curves
defined over the rational numbers.

mwrank is a program written in C++ for computing Mordell-Weil groups of
elliptic curves over Q via 2-descent. It is available as source code in
the eclib package, which may be distributed under the GNU General Public
License, version 2, or any later version.

mwrank is now only distributed as part of eclib. eclib is also included
in Sage, and for most potential users the easiest way to run mwrank is
to install Sage (which also of course gives you much much more). I no
longer provide a source code distribution of mwrank by itself: use eclib
instead.

License
-------

eclib is licensed GPL v2+.


Upstream Contact
----------------

-  Author: John Cremona
-  Email: john.cremona@gmail.com
-  Website:
   https://johncremona.github.io/mwrank/index.html
-  Repository: https://github.com/JohnCremona/eclib


Type
----

standard


Dependencies
------------

- :ref:`spkg_flint`
- :ref:`spkg_ntl`
- :ref:`spkg_pari`

Version Information
-------------------

package-version.txt::

    20250627

See https://repology.org/project/eclib/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i eclib

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S eclib

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install eclib

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libec-dev eclib-tools

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install eclib eclib-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/eclib

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge sci-mathematics/eclib\[flint\]

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr eclib

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install eclib-devel


If the system package is installed, ``./configure`` will check if it can be used.
