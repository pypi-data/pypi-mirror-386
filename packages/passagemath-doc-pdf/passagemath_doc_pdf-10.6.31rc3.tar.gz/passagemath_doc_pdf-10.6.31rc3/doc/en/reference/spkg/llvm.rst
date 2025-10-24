.. _spkg_llvm:

llvm: The LLVM Compiler Infrastructure, including the Clang C/C++/Objective-C compiler
======================================================================================

Description
-----------

The LLVM Project is a collection of modular and reusable compiler and toolchain technologies.

Clang is an "LLVM native" C/C++/Objective-C compiler.

The libc++ and libc++ ABI projects provide a standard conformant and high-performance
implementation of the C++ Standard Library, including full support for C++11 and C++14.

License
-------

Apache 2.0 License with LLVM exceptions

Upstream Contact
----------------

https://llvm.org/


Type
----

optional


Dependencies
------------




Installation commands
---------------------

.. tab:: Sage distribution:

   This is a dummy package and cannot be installed using the Sage distribution.

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add clang

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S clang

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install clang

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install clang

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install devel/llvm

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge sys-devel/clang

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install llvm

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install clang

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr clang

.. tab:: OpenBSD:

   install the following packages: devel/llvm

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install llvm

.. tab:: Slackware:

   .. CODE-BLOCK:: bash

       $ sudo slackpkg install llvm

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install clang


If the system package is installed, ``./configure`` will check if it can be used.
