.. _spkg_maxima:

maxima: System for manipulating symbolic and numerical expressions
==================================================================

Description
-----------

Maxima is a system for the manipulation of symbolic and numerical
expressions, including differentiation, integration, Taylor series,
Laplace transforms, ordinary differential equations, systems of linear
equations, polynomials, and sets, lists, vectors, matrices, and tensors.
Maxima yields high precision numeric results by using exact fractions,
arbitrary precision integers, and variable precision floating point
numbers. Maxima can plot functions and data in two and three dimensions.

For more information, see the Maxima web site

http://maxima.sourceforge.net

License
-------

Maxima is distributed under the GNU General Public License, with some
export restrictions from the U.S. Department of Energy. See the file
COPYING.


Upstream Contact
----------------

-  The Maxima mailing list - see
   http://maxima.sourceforge.net/maximalist.html

Special Update/Build Instructions
---------------------------------

1. Go to http://sourceforge.net/projects/maxima/files/Maxima-source/
   and download the source tarball maxima-x.y.z.tar.gz; place it in
   the upstream/ directory.

2. Update package-version.txt and run 'sage --package fix-checksum'.

3. Make sure the patches still apply cleanly, and update them if
   necessary.

4. Test the resulting package.

All patch files in the patches/ directory are applied. Descriptions of
these patches are either in the patch files themselves or below.

-  infodir.patch: Correct the path to the Info directory. Introduced
   in Issue #11348 (maxima test fails when install tree is moved).


Type
----

standard


Dependencies
------------

- :ref:`spkg_ecl`
- :ref:`spkg_info`

Version Information
-------------------

package-version.txt::

    5.47.0

See https://repology.org/project/maxima/versions, https://repology.org/project/maxima-ecl/versions, https://repology.org/project/maxima-sage/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i maxima

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S maxima-fas

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install maxima

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install maxima-sage maxima

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install maxima-runtime-ecl maxima

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/maxima

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge sci-mathematics/maxima\[ecl\]

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install maxima

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install maxima

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr maxima-ecl

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install maxima-ecl


If the system package is installed, ``./configure`` will check if it can be used.
