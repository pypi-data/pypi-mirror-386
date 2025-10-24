.. _spkg__bootstrap:

_bootstrap: Represents system packages required for running the top-level bootstrap script
==========================================================================================

Description
-----------

This optional script package represents the requirements (system packages)
that are needed in addition to those represented by the ``_prereq`` package
in order to run the top-level ``bootstrap`` script.


Type
----

optional


Dependencies
------------




Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i _bootstrap

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add bash gettext-dev autoconf automake libtool pkgconf

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S autoconf automake libtool pkgconf

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install autoconf automake libtool pkg-config

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install autoconf automake libtool pkg-config

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install autoconf automake libtool pkg-config

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install autoconf automake libtool pkg-config

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-build/autoconf dev-build/automake dev-build/libtool

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install autoconf automake libtool pkg-config

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install gettext autoconf automake libtool pkgconfig

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S autoconf automake libtool pkg-config

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr autoconf automake libtool pkg-config

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install autoconf automake libtool pkgconfig

.. tab:: Slackware:

   .. CODE-BLOCK:: bash

       $ sudo slackpkg install autoconf automake libtool pkg-config

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install autoconf automake libtool xtools mk-configure \
             pkg-config


