.. _spkg_perl_term_readline_gnu:

perl_term_readline_gnu: Perl extension for the GNU Readline/History libraries
=============================================================================

Description
-----------

Perl extension for the GNU Readline/History Library

Available on CPAN

License
-------

The Perl 5 License (Artistic 1 & GPL 1)


Upstream Contact
----------------

Hiroo HAYASHI



Type
----

optional


Dependencies
------------

- :ref:`spkg_readline`

Version Information
-------------------

package-version.txt::

    1.35

See https://repology.org/project/perl:term-readline-gnu/versions, https://repology.org/project/perl:termreadline-gnu/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i perl_term_readline_gnu

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add perl-term-readline-gnu

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S perl-term-readline-gnu

.. tab:: cpan:

   .. CODE-BLOCK:: bash

       $ cpan -i Term::ReadLine::Gnu

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libterm-readline-gnu-perl

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install perl-Term-ReadLine-Gnu

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install devel/p5-Term-ReadLine-Gnu

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-perl/Term-ReadLine-Gnu

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install p5-term-readline-gnu

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install perl\(Term::ReadLine::Gnu\)

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install perl-Term-ReadLine-Gnu


If the system package is installed, ``./configure`` will check if it can be used.
