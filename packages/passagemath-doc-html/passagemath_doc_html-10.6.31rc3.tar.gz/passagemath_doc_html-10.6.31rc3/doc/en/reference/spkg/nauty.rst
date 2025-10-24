.. _spkg_nauty:

nauty: Find automorphism groups of graphs, generate non-isomorphic graphs
=========================================================================

Description
-----------

Nauty has various tools for finding the automorphism group of a graph,
generating non-isomorphic graphs with certain properties, etc.

License
-------

Since version 2.6, nauty license is GPL-compatible, see

http://users.cecs.anu.edu.au/~bdm/nauty/COPYRIGHT.txt

(a copy of this file, called COPYRIGHT, is also present in the tarball)

Upstream Contact
----------------

Brendan D. McKay, Computer Science Department Australian National
University bdm@cs.anu.edu.au

Adolfo Piperno, Dipartimento di Informatica Sapienza - Università di Roma
piperno@di.uniroma1.it

See https://users.cecs.anu.edu.au/~bdm/nauty/ or https://pallini.di.uniroma1.it/


Type
----

standard


Dependencies
------------



Version Information
-------------------

package-version.txt::

    2.9.1

See https://repology.org/project/nauty/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i nauty

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S nauty

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install nauty

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install nauty

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install nauty

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/nauty

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install nauty

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr nauty

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install nauty nauty-devel

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install nauty


If the system package is installed, ``./configure`` will check if it can be used.
