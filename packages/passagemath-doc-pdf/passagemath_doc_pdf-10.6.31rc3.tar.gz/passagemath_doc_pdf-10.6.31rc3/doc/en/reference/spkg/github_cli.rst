.. _spkg_github_cli:

github_cli: Command-line interface for GitHub
=============================================

Description
-----------

``gh`` is GitHub on the command line. It brings pull requests, issues, and
other GitHub concepts to the terminal next to where you are already
working with ``git`` and your code.

License
-------

MIT

Upstream Contact
----------------

https://github.com/cli/cli


Type
----

optional


Dependencies
------------



Version Information
-------------------

See https://repology.org/project/github-cli/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   This is a dummy package and cannot be installed using the Sage distribution.

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add github-cli

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S github-cli

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install gh

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install gh

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install gh

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install devel/gh

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-util/github-cli

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install gh

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install gh

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr gh

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install gh

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install github-cli


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
