.. _spkg_texlive:

texlive: A comprehensive TeX system
===================================

Description
-----------

TeX Live is an easy way to get up and running with the TeX document
production system. It provides a comprehensive TeX system with binaries
for most flavors of Unix, including GNU/Linux, and also Windows. It
includes all the major TeX-related programs, macro packages, and fonts
that are free software, including support for many languages around the
world.

This package installs all texlive packages required to build Sage. If
necessary, texlive itself is installed.

License
-------

Various FSF-approved free software licenses. See
https://www.tug.org/texlive/copying.html for details.


Upstream Contact
----------------

Home page: https://www.tug.org/texlive

Dependencies
------------

-  python


Special Update/Build Instructions
---------------------------------

This package requires internet access to download texlive packages for
the TeX mirrors.


Type
----

optional


Dependencies
------------



Version Information
-------------------

See https://repology.org/project/texlive/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i texlive

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add texlive

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S texlive-core texlive-latexextra texlive-langjapanese \
             texlive-langcyrillic texlive-langchinese

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install texlive-latex-extra texlive-xetex latexmk dvipng \
             tex-gyre texlive-fonts-recommended texlive-lang-cyrillic \
             texlive-lang-english texlive-lang-european texlive-lang-french \
             texlive-lang-german texlive-lang-italian texlive-lang-japanese \
             texlive-lang-polish texlive-lang-portuguese texlive-lang-spanish \
             texlive-lang-chinese

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install latexmk texlive texlive-collection-latexextra \
             texlive-collection-langcyrillic texlive-collection-langeuropean \
             texlive-collection-langfrench texlive-collection-langgerman \
             texlive-collection-langitalian texlive-collection-langjapanese \
             texlive-collection-langpolish texlive-collection-langportuguese \
             texlive-collection-langspanish texlive-collection-langcjk

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-tex/latexmk app-text/texlive app-text/dvipng \
             dev-texlive/texlive-langcjk dev-texlive/texlive-langcyrillic \
             dev-texlive/texlive-langenglish dev-texlive/texlive-langeuropean \
             dev-texlive/texlive-langfrench dev-texlive/texlive-langgerman \
             dev-texlive/texlive-langitalian dev-texlive/texlive-langjapanese \
             dev-texlive/texlive-langportuguese \
             dev-texlive/texlive-langspanish dev-texlive/texlive-latexextra \
             dev-texlive/texlive-latexrecommended \
             dev-texlive/texlive-mathscience dev-texlive/texlive-langchinese

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install texlive

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S -texlive-full

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install texlive

.. tab:: Slackware:

   .. CODE-BLOCK:: bash

       $ sudo slackpkg install texlive

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install texlive


If the system package is installed, ``./configure`` will check if it can be used.
