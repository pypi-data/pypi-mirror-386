.. _spkg_liblzma:

liblzma: General-purpose data compression software
==================================================

Description
-----------

This packages represents liblzma, a part of XZ Utils, the free general-purpose
data compression software with a high compression ratio.

License
-------

Some parts public domain, other parts GNU LGPLv2.1, GNU GPLv2, or GNU
GPLv3.


Upstream Contact
----------------

http://tukaani.org/xz/



Type
----

standard


Dependencies
------------



Version Information
-------------------

package-version.txt::

    5.2.10

See https://repology.org/project/xz/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i liblzma

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add xz-dev

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install xz

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install xz-utils liblzma-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install xz xz-devel

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install xz

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install xz

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install xz pkgconfig\(liblzma\)

.. tab:: pyodide:

   install the following packages: liblzma

.. tab:: Slackware:

   .. CODE-BLOCK:: bash

       $ sudo slackpkg install xz

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install xz liblzma-devel


If the system package is installed, ``./configure`` will check if it can be used.
