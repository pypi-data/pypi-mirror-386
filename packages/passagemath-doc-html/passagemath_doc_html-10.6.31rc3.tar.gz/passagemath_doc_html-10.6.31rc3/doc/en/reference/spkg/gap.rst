.. _spkg_gap:

gap: Groups, Algorithms, Programming - a system for computational discrete algebra
==================================================================================

Description
-----------

GAP is a system for computational discrete algebra, with particular
emphasis on Computational Group Theory. GAP provides a programming
language, a library of thousands of functions implementing algebraic
algorithms written in the GAP language as well as large data libraries
of algebraic objects. See also the overview and the description of the
mathematical capabilities. GAP is used in research and teaching for
studying groups and their representations, rings, vector spaces,
algebras, combinatorial structures, and more. The system, including
source, is distributed freely. You can study and easily modify or extend
it for your special use.

This is a stripped-down version of GAP. The databases, which are
architecture-independent, are in a separate package.


Upstream Contact
----------------

https://www.gap-system.org

Mailing list at https://mail.gap-system.org/mailman/listinfo/gap


Type
----

standard


Dependencies
------------

- $(MP_LIBRARY)
- :ref:`spkg_ncurses`
- :ref:`spkg_readline`
- :ref:`spkg_zlib`

Version Information
-------------------

package-version.txt::

    4.15.1

See https://repology.org/project/gap/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i gap

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S gap

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install gap-defaults

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install gap libgap-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install gap gap-core gap-devel gap-libs libgap xgap \
             gap-pkg-ace gap-pkg-aclib gap-pkg-alnuth gap-pkg-anupq \
             gap-pkg-atlasrep gap-pkg-autodoc gap-pkg-automata gap-pkg-autpgrp \
             gap-pkg-browse gap-pkg-caratinterface gap-pkg-circle \
             gap-pkg-congruence gap-pkg-crisp gap-pkg-crypting \
             gap-pkg-crystcat gap-pkg-curlinterface gap-pkg-cvec \
             gap-pkg-datastructures gap-pkg-digraphs gap-pkg-edim \
             gap-pkg-ferret gap-pkg-fga gap-pkg-fining gap-pkg-float \
             gap-pkg-format gap-pkg-forms gap-pkg-fplsa gap-pkg-fr \
             gap-pkg-francy gap-pkg-genss gap-pkg-groupoids gap-pkg-grpconst \
             gap-pkg-images gap-pkg-io gap-pkg-irredsol gap-pkg-json \
             gap-pkg-jupyterviz gap-pkg-lpres gap-pkg-nq gap-pkg-openmath \
             gap-pkg-orb gap-pkg-permut gap-pkg-polenta gap-pkg-polycyclic \
             gap-pkg-primgrp gap-pkg-profiling gap-pkg-radiroot gap-pkg-recog \
             gap-pkg-resclasses gap-pkg-scscp gap-pkg-semigroups \
             gap-pkg-singular gap-pkg-smallgrp gap-pkg-smallsemi \
             gap-pkg-sophus gap-pkg-spinsym gap-pkg-standardff gap-pkg-tomlib \
             gap-pkg-transgrp gap-pkg-transgrp-data gap-pkg-utils gap-pkg-uuid \
             gap-pkg-xmod gap-pkg-zeromqinterface

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/gap

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge sci-mathematics/gap

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr gap


If the system package is installed, ``./configure`` will check if it can be used.
