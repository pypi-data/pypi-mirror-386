.. _spkg_openssl:

openssl: Implementation of the SSL and TLS protocols
====================================================

Description
-----------

From wikipedia: OpenSSL is an open source implementation of the SSL and
TLS protocols. The core library (written in the C programming language)
implements the basic cryptographic functions and provides various
utility functions. Wrappers allowing the use of the OpenSSL library in a
variety of computer languages are available.

License
-------

- Apache License v2 (considered compatible with GPL v3)


Upstream Contact
----------------

-  http://openssl.org/


Type
----

standard


Dependencies
------------



Version Information
-------------------

package-version.txt::

    3.2.4

See https://repology.org/project/openssl/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i openssl

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add openssl-dev

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S openssl

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install openssl

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install openssl libssl-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install openssl openssl-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install security/openssl

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install openssl

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install openssl

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr openssl

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install libopenssl-3-devel

.. tab:: pyodide:

   install the following packages: openssl

.. tab:: Slackware:

   .. CODE-BLOCK:: bash

       $ sudo slackpkg install openssl openssl-solibs

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install openssl-devel


If the system package is installed, ``./configure`` will check if it can be used.
