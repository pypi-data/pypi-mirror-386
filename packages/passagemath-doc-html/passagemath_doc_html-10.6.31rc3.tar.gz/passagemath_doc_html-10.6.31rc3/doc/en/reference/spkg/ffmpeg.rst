.. _spkg_ffmpeg:

ffmpeg: ffmpeg video converter
==============================

Description
-----------

ffmpeg is a very fast video and audio converter that can also grab from a live
audio/video source. It can also convert between arbitrary sample rates and
resize video on the fly with a high quality polyphase filter.

License
-------

"FFmpeg is licensed under the GNU Lesser General Public License (LGPL) version
2.1 or later. However, FFmpeg incorporates several optional parts and
optimizations that are covered by the GNU General Public License (GPL) version
2 or later. If those parts get used the GPL applies to all of FFmpeg."

http://ffmpeg.org/legal.html

Upstream Contact
----------------

http://ffmpeg.org/



Type
----

optional


Dependencies
------------



Version Information
-------------------

See https://repology.org/project/ffmpeg/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   This is a dummy package and cannot be installed using the Sage distribution.

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add ffmpeg

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S ffmpeg

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install imageio-ffmpeg

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install ffmpeg

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install ffmpeg-free ffmpeg-free-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install multimedia/ffmpeg

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install ffmpeg

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install ffmpeg

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S -ffmpeg

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr ffmpeg

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install ffmpeg

.. tab:: pyodide:

   install the following packages: ffmpeg

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install ffmpeg


If the system package is installed, ``./configure`` will check if it can be used.
