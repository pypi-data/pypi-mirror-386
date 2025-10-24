.. _spkg_libbraiding:

libbraiding: Computing with braids
==================================

Description
-----------

libbraiding is a library to compute several properties of braids,
including centralizer and conjugacy check.

License
-------

GPLv3+


Upstream Contact
----------------

Miguel Marco (mmarco@unizar.es)

https://github.com/miguelmarco/libbraiding


Type
----

standard


Dependencies
------------



Version Information
-------------------

package-version.txt::

    1.3.1

See https://repology.org/project/libbraiding/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i libbraiding

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S libbraiding

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install libbraiding

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libbraiding-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install libbraiding-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/libbraiding

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge sci-libs/libbraiding

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr libbraiding

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install libbraiding-devel

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install libbraiding-devel


If the system package is installed, ``./configure`` will check if it can be used.
