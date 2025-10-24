.. _spkg_cliquer:

cliquer: Routines for clique searching
======================================

Description
-----------

Cliquer is a set of C routines for finding cliques in an arbitrary
weighted graph. It uses an exact branch-and-bound algorithm
developed by Patric Östergård.

License
-------

GNU General Public License v2


Upstream Contact
----------------

Cliquer was mainly written by Sampo Niskanen, sampo.niskanenQiki.fi
(Q=@).

https://users.aalto.fi/~pat/cliquer.html

Patches
-------

-  minor config updates (v1.22)
-  autotoolized - see https://github.com/dimpase/autocliquer (v1.21)


Type
----

standard


Dependencies
------------



Version Information
-------------------

package-version.txt::

    1.23

See https://repology.org/project/cliquer/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i cliquer

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S cliquer

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install cliquer

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install cliquer libcliquer-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install cliquer cliquer-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/cliquer

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge sci-mathematics/cliquer

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr cliquer

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install cliquer cliquer-devel

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install cliquer-devel


If the system package is installed, ``./configure`` will check if it can be used.
