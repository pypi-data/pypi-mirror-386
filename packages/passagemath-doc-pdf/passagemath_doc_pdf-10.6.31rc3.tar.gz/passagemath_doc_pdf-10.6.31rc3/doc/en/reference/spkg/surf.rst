.. _spkg_surf:

surf: Visualization of algebraic curves, algebraic surfaces and hyperplane sections of surfaces
===============================================================================================

Description
-----------

surf is a tool to visualize some real algebraic geometry: plane
algebraic curves, algebraic surfaces and hyperplane sections of
surfaces. surf is script driven and has (optionally) a nifty GUI using
the Gtk widget set.

This is used by the Singular Jupyter kernel to produce 3D plots.

License
-------

GPL version 2 or later


Upstream Contact
----------------

http://surf.sourceforge.net (although the project is essentially dead)

Dependencies
------------

-  cups (optional)
-  GNU flex Version 2.5 or higher
-  GTK+ Version 1.2.0 or higher (optional)
-  POSIX Threads
-  GNU MP(gmp) Version 2 or higher
-  lib-tiff
-  lib-jpeg
-  zlib
-  ps2pdf (optional)

This package is "experimental" because not all of these dependencies are
packaged with Sage.


Type
----

experimental


Dependencies
------------

- $(MP_LIBRARY)
- :ref:`spkg_flex`

Version Information
-------------------

package-version.txt::

    1.0.6-gcc6

See https://repology.org/project/surf-alggeo/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i surf

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install surf-alggeo

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install surf-geometry

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install surf


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
