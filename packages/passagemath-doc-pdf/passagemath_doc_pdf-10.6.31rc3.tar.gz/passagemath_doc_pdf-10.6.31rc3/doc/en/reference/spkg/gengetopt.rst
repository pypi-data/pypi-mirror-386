.. _spkg_gengetopt:

gengetopt: getopt_long parser generator
===========================================

Description
-----------

GNU Gengetopt converts a textual description of your program's
arguments and options into a getopt_long() parser in C (or C++).

Website: https://www.gnu.org/software/gengetopt/


License
-------
GPL-3+ (https://www.gnu.org/software/gengetopt/LICENSE)


Type
----

standard


Dependencies
------------

- :ref:`spkg_xz`

Version Information
-------------------

package-version.txt::

    2.23

See https://repology.org/project/gengetopt/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i gengetopt

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add gengetopt

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install gengetopt

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install gengetopt

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install gengetopt

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-util/gengetopt

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install gengetopt

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr gengetopt

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install gengetopt


If the system package is installed, ``./configure`` will check if it can be used.
