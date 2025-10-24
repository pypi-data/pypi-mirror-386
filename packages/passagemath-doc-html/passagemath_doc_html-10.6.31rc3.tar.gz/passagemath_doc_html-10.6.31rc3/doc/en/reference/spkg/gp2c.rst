.. _spkg_gp2c:

gp2c: A compiler for translating GP routines to C
=================================================

Description
-----------

The gp2c compiler is a package for translating GP routines into the C
programming language, so that they can be compiled and used with the
PARI system or the GP calculator.

License
-------

GPL version 2+


Upstream Contact
----------------

-  http://pari.math.u-bordeaux.fr/

Dependencies
------------

-  PARI
-  Perl


Type
----

optional


Dependencies
------------

- :ref:`spkg_pari`

Version Information
-------------------

package-version.txt::

    0.0.14

See https://repology.org/project/gp2c/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i gp2c

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install pari-gp2c

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install gp2c

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/gp2c

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge sci-mathematics/gp2c

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install gp2c

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install gp2c


If the system package is installed, ``./configure`` will check if it can be used.
