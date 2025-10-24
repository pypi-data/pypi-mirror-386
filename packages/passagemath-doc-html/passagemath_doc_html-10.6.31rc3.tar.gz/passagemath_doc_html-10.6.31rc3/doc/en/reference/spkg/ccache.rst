.. _spkg_ccache:

ccache: A compiler cache
========================

Description
-----------

ccache is a compiler cache. It speeds up recompilation by caching
previous compilations and detecting when the same compilation is being
done again. Supported languages are C, C++, Objective-C and
Objective-C++.

License
-------

GNU General Public License version 3 or later


Upstream Contact
----------------

-  Author: Andrew Tridgell
-  Website: http://ccache.samba.org/


Type
----

optional


Dependencies
------------

- :ref:`spkg_cmake`
- :ref:`spkg_ninja_build`
- :ref:`spkg_xz`

Version Information
-------------------

package-version.txt::

    4.10.2

See https://repology.org/project/ccache/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i ccache

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S ccache

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install ccache

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install ccache

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install ccache

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install ccache

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install ccache

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install ccache


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
