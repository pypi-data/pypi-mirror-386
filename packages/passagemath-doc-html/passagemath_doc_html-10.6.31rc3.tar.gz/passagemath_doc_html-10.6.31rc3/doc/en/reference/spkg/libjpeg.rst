.. _spkg_libjpeg:

libjpeg: JPEG image support
===========================

Description
-----------

This dummy package represents the image library ``libjpeg``.

We do not have an SPKG for it. The purpose of this dummy package is to
associate system package lists with it.

If the system package is installed, the package ``pillow`` will include
support for JPEG images.


Type
----

optional


Dependencies
------------




Installation commands
---------------------

.. tab:: Sage distribution:

   This is a dummy package and cannot be installed using the Sage distribution.

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add libjpeg-turbo-dev

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S libjpeg-turbo

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libjpeg-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install libjpeg-turbo-devel

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge media-libs/libjpeg-turbo

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install jpeg-turbo

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr libjpeg-turbo

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install libjpeg-devel

.. tab:: Slackware:

   .. CODE-BLOCK:: bash

       $ sudo slackpkg install libjpeg-turbo

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install libjpeg-turbo-devel


If the system package is installed, ``./configure`` will check if it can be used.
