.. _spkg_imagemagick:

imagemagick: A collection of tools and libraries for many image file formats
============================================================================

Description
-----------

A collection of tools and libraries for many image file formats

License
-------

Copyright [yyyy] [name of copyright owner]

Licensed under the ImageMagick License (the "License"); you may not use
this file except in compliance with the License.  You may obtain a copy
of the License at

    https://imagemagick.org/script/license.php

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
License for the specific language governing permissions and limitations
under the License.

Upstream Contact
----------------

http://www.imagemagick.org/


Type
----

optional


Dependencies
------------



Version Information
-------------------

See https://repology.org/project/imagemagick/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   This is a dummy package and cannot be installed using the Sage distribution.

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add imagemagick

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S imagemagick

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install imagemagick

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install imagemagick

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install ImageMagick

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install graphics/ImageMagick7

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install imagemagick

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install ImageMagick

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr imagemagick

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install ImageMagick

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install ImageMagick


If the system package is installed, ``./configure`` will check if it can be used.
