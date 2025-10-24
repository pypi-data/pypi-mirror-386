.. _spkg_bliss:

bliss: Computing automorphism groups and canonical forms of graphs
==================================================================

Description
-----------

bliss is an open source tool for computing automorphism groups and
canonical forms of graphs.

License
-------

LGPL3


Upstream Contact
----------------

Bliss is currently being maintained by Tommi Junttila at

https://users.aalto.fi/~tjunttil/bliss/index.html

Bliss used to be maintained by Tommi Junttila and Petteri Kaski up to version 0.73 at

http://www.tcs.tkk.fi/Software/bliss/index.html


Type
----

optional


Dependencies
------------

- :ref:`spkg_cmake`
- :ref:`spkg_ninja_build`

Version Information
-------------------

package-version.txt::

    0.77

See https://repology.org/project/bliss-graphs/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i bliss

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add bliss

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S bliss

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install bliss\>=0.77

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install bliss bliss-devel

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge sci-libs/bliss

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install bliss bliss-devel


If the system package is installed, ``./configure`` will check if it can be used.
