.. _spkg__prereq:

_prereq: Represents system packages required for installing SageMath from source
================================================================================

Description
-----------

This dummy package represents the minimal requirements (system packages)
for installing SageMath from source.

In addition to standard :wikipedia:`POSIX <POSIX>` utilities
and the :wikipedia:`bash <Bash_(Unix_shell)>` shell,
the following standard command-line development tools must be installed on your
computer:

- **make**: GNU make, version 3.80 or later. Version 3.82 or later is recommended.
- **m4**: GNU m4 1.4.2 or later (non-GNU or older versions might also work).
- **perl**: version 5.8.0 or later.
- **ar** and **ranlib**: can be obtained as part of GNU binutils.
- **tar**: GNU tar version 1.17 or later, or BSD tar (as provided on macOS).
- **python**: Python 3.4 or later, or Python 2.7.
  (This range of versions is a minimal requirement for internal purposes of the SageMath
  build system, which is referred to as ``sage-bootstrap-python``.)

Other versions of these may work, but they are untested.

On macOS, suitable versions of all of these tools are provided
by the Xcode Command Line Tools.  To install them, open a terminal
window and run ``xcode-select --install``; then click "Install" in the
pop-up window.  If the Xcode Command Line Tools are already installed,
you may want to check if they need to be updated by typing
``softwareupdate -l``.

On Linux, ``ar`` and ``ranlib`` are in the `binutils
<https://www.gnu.org/software/binutils/>`_ package.  The other
programs are usually located in packages with their respective names.

On Redhat-derived systems not all perl components are installed by
default and you might have to install the ``perl-ExtUtils-MakeMaker``
package.

To check if you have the above prerequisites installed, for example ``perl``,
type::

    $ command -v perl

or::

    $ which perl

on the command line. If it gives an error (or returns nothing), then
either ``perl`` is not installed, or it is installed but not in your
:wikipedia:`PATH <PATH_%28variable%29>`.


Type
----

standard


Dependencies
------------




Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i _prereq

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add binutils make m4 perl python3 tar bc gcc g++ ca-certificates \
             coreutils flex bison linux-headers

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S binutils make m4 perl python tar bc gcc flex which \
             bison

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install compilers make m4 perl python tar bc flex bison

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install binutils make m4 perl flex bison python3 tar bc \
             gcc g++ ca-certificates

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install binutils make m4 gawk python3 perl \
             perl-ExtUtils-MakeMaker tar gcc gcc-c++ findutils which diffutils \
             perl-IPC-Cmd flex bison

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install gmake automake bash dash python flex bison

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge sys-devel/binutils sys-libs/binutils-libs dev-build/make \
             dev-scheme/guile dev-libs/libffi app-arch/tar sys-devel/gcc \
             dev-libs/mpc sys-libs/glibc sys-kernel/linux-headers \
             dev-lang/perl sys-devel/m4 sys-devel/bc dev-lang/python \
             app-misc/ca-certificates dev-libs/libxml2 sys-apps/findutils \
             sys-apps/which sys-apps/diffutils sys-devel/flex sys-devel/bison

.. tab:: Homebrew:

   No package needed

.. tab:: MacPorts:

   No package needed

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S binutils make m4 perl python tar bc gcc which

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr binutils gnumake gnum4 perl python3 gnutar bc gcc bash flex bison

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install binutils make m4 gawk perl python3 tar bc which \
             glibc-locale-base gcc gcc-c++ ca-certificates gzip findutils \
             diffutils flex bison

.. tab:: Slackware:

   .. CODE-BLOCK:: bash

       $ sudo slackpkg install binutils make guile gc libffi gcc-13 gcc-g++-13 \
             libmpc glibc kernel-headers perl m4 bc python3 flex \
             ca-certificates libxml2 cyrus-sasl bison

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install bc binutils gcc libgomp-devel m4 make perl python3 \
             tar bash which diffutils gzip python3-devel bzip2-devel xz \
             liblzma-devel libffi-devel zlib-devel libxcrypt-devel flex bison


If the system package is installed, ``./configure`` will check if it can be used.
