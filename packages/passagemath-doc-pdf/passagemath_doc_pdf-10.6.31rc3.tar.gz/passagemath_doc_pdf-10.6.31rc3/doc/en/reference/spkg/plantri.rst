.. _spkg_plantri:

plantri: Generate non-isomorphic sphere-embdedded graphs
========================================================

Description
-----------

Plantri is a program that generates certain types of graphs that are
imbedded on the sphere.

Exactly one member of each isomorphism class is output, using an amount
of memory almost independent of the number of graphs produced. This,
together with the exceptionally fast operation and careful validation,
makes the program suitable for processing very large numbers of graphs.

Isomorphisms are defined with respect to the embeddings, so in some
cases outputs may be isomorphic as abstract graphs.

License
-------

Apache License, Version 2.0


Upstream Contact
----------------

Gunnar Brinkmann

- University of Ghent
- Gunnar.Brinkmann@ugent.be

Brendan McKay

- Australian National University
- bdm@cs.anu.edu.au

See https://users.cecs.anu.edu.au/~bdm/plantri/


Type
----

optional


Dependencies
------------



Version Information
-------------------

package-version.txt::

    5.5

See https://repology.org/project/plantri/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i plantri

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S plantri

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install plantri


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
