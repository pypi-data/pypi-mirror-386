.. _spkg_libhomfly:

libhomfly: Compute the homfly polynomial of knots and links
===========================================================

Description
-----------

libhomfly is a library to compute the homfly polynomial of knots and
links.

License
-------

Public domain


Upstream Contact
----------------

Miguel Marco (mmarco@unizar.es)

https://github.com/miguelmarco/libhomfly


Type
----

standard


Dependencies
------------

- :ref:`spkg_gc`

Version Information
-------------------

package-version.txt::

    1.03

See https://repology.org/project/libhomfly/versions, https://repology.org/project/llibhomfly/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i libhomfly

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S libhomfly

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install libhomfly

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libhomfly-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install libhomfly-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/libhomfly

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge sci-libs/libhomfly

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr libhomfly

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install libhomfly-devel

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install libhomfly-devel


If the system package is installed, ``./configure`` will check if it can be used.
