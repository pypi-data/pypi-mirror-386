.. _spkg_patchelf:

patchelf: A small utility to modify the dynamic linker and RPATH of ELF executables
===================================================================================

Description
-----------

A small utility to modify the dynamic linker and RPATH of ELF executables.

License
-------

GPL-3.0-or-later

Upstream Contact
----------------

https://github.com/NixOS/patchelf


Type
----

standard


Dependencies
------------

- :ref:`spkg__bootstrap`
- :ref:`spkg_bzip2`

Version Information
-------------------

package-version.txt::

    523f401584d9584e76c9c77004e7abeb9e6c4551

See https://repology.org/project/patchelf/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i patchelf

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install patchelf

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install patchelf

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install patchelf

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install sysutils/patchelf

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-util/patchelf

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install patchelf

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install patchelf

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr patchelf

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install patchelf

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install patchelf


If the system package is installed, ``./configure`` will check if it can be used.
