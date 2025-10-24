.. _spkg_linbox:

linbox: Linear algebra with dense, sparse, structured matrices over the integers and finite fields
==================================================================================================

Description
-----------

LinBox is a C++ template library for exact,
high-performance linear algebra computation with dense, sparse, and
structured matrices over the integers and over finite fields.

License
-------

LGPL V2 or later


Upstream Contact
----------------

-  https://linalg.org/
-  <linbox-devel@googlegroups.com>
-  <linbox-use@googlegroups.com>


Type
----

standard


Dependencies
------------

- $(MP_LIBRARY)
- :ref:`spkg_fflas_ffpack`
- :ref:`spkg_flint`
- :ref:`spkg_givaro`
- :ref:`spkg_iml`
- :ref:`spkg_mpfr`
- :ref:`spkg_ntl`

Version Information
-------------------

package-version.txt::

    1.7.1.p1

See https://repology.org/project/linbox/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i linbox

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S linbox

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install linbox

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install liblinbox-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install linbox linbox-devel

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/linbox

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge sci-libs/linbox

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr linbox

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install pkgconfig\(linbox\)

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install linbox-devel


If the system package is installed, ``./configure`` will check if it can be used.
