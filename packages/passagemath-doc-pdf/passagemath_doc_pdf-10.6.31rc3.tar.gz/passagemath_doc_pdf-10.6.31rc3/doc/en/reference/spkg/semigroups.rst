.. _spkg_semigroups:

semigroups: An optional GAP package
===================================

Description
-----------

Installing this SPKG will install the corresponding GAP package, but
before you can use them in Sage, they still have to be loaded into
either the GAP interface or libgap::

  sage: gap.eval('LoadPackage("semigroups")')  # optional - semigroups
  'true'
  sage: libgap.LoadPackage("semigroups")       # optional - semigroups
  true

Those correspond to::

  gap> LoadPackage("semigroups");

within the GAP interface and libgap, respectively.

Upstream Contact
----------------

See https://semigroups.github.io/Semigroups/

Dependencies
------------

-  GAP (a standard spkg), gap_packages and libsemigroups (optional packages)

Notes
-----------
This is a GAP package for semigroups, and monoids. There are
particularly efficient methods for finitely presented semigroups and monoids,
and for semigroups and monoids consisting of transformations, partial
permutations, bipartitions, partitioned binary relations, subsemigroups of
regular Rees 0-matrix semigroups, and matrices of various semirings including
boolean matrices, matrices over finite fields, and certain tropical matrices.
Semigroups contains efficient methods for creating semigroups, monoids, and
inverse semigroups and monoids, calculating their Green's structure, ideals,
size, elements, group of units, small generating sets, testing membership,
finding the inverses of a regular element, factorizing elements over the
generators, and so on. It is possible to test if a semigroup satisfies a
particular property, such as if it is regular, simple, inverse, completely
regular, and a large number of further properties. There are methods for
finding presentations for a semigroup, the congruences of a semigroup, the
maximal subsemigroups of a finite semigroup, smaller degree partial
permutation representations, and the character tables of inverse semigroups.
There are functions for producing pictures of the Green's structure of a
semigroup, and for drawing graphical representations of certain types of
elements.
(Authors: James Mitchell, Marina Anagnostopoulou-Merkouri,
Thomas Breuer, Stuart Burrell, Reinis Cirpons, Tom Conti-Leslie,
Joseph Edwards, Attila Egri-Nagy, Luke Elliott, Fernando Flores Brito,
Tillman Froehlich, Nick Ham, Robert Hancock, Max Horn, Christopher Jefferson,
Julius Jonusas, Chinmaya Nagpal, Olexandr Konovalov, Artemis Konstantinidi,
Hyeokjun Kwon, Dima V. Pasechnik, Markus Pfeiffer, Christopher Russell,
Jack Schmidt, Sergio Siccha, Finn Smith, Ben Spiers, Nicolas Thiéry,
Maria Tsalakou, Chris Wensley, Murray Whyte, Wilf A. Wilson, Tianrun Yang,
Michael Young and Fabian Zickgraf)


Type
----

optional


Dependencies
------------

- :ref:`spkg_gap`
- :ref:`spkg_gap_packages`
- :ref:`spkg_libsemigroups`

Version Information
-------------------

package-version.txt::

    5.5.3

See https://repology.org/project/gap/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i semigroups

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install gap

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install gap-pkg-cohomolo gap-pkg-corelg gap-pkg-crime \
             gap-pkg-cryst gap-pkg-ctbllib gap-pkg-design gap-pkg-factint \
             GAPDoc gap-pkg-gbnp gap-pkg-grape gap-pkg-guava gap-pkg-hap \
             gap-pkg-hapcryst gap-pkg-hecke gap-pkg-laguna gap-pkg-liealgdb \
             gap-pkg-liepring gap-pkg-liering gap-pkg-loops gap-pkg-mapclass \
             gap-pkg-polymaking gap-pkg-qpa gap-pkg-quagroup gap-pkg-repsn \
             gap-pkg-sla gap-pkg-sonata gap-pkg-toric

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-gap/semigroups


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
