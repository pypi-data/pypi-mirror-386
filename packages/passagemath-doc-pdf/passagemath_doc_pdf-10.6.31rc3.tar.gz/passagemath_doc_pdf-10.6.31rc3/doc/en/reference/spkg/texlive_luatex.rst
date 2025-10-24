.. _spkg_texlive_luatex:

texlive_luatex: LuaTeX packages
===============================

Description
-----------

Packages for LuaTeX, a TeX engine using Lua as an embedded scripting and
extension language, with native support for Unicode, OpenType/TrueType fonts,
and both PDF and DVI output.

The purpose of this dummy package is to associate system package lists with it.

License
-------

GNU General Public License version 2.0 (GPLv2)

Upstream Contact
----------------

https://www.luatex.org/


Type
----

optional


Dependencies
------------

- :ref:`spkg_texlive`

Version Information
-------------------

See https://repology.org/project/texlive-luatex/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   This is a dummy package and cannot be installed using the Sage distribution.

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add texlive-luatex

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S texlive-luatex

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install texlive-luatex

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install texlive-luatex

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-texlive/texlive-luatex

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install texlive-luatex

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install texlive-luatex


If the system package is installed, ``./configure`` will check if it can be used.
