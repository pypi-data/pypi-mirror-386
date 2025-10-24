.. _spkg_saclib:

saclib: Computations with real algebraic numbers
================================================

Description
-----------

Saclib is a library of C programs for computer algebra derived from the
SAC2 system. It is mainly used as a dependency of qepcad.

License
-------

ICS :wikipedia:`ISC_license`

Upstream Contact
----------------

- Repository: https://github.com/chriswestbrown/saclib
- Tarballs:   https://www.usna.edu/Users/cs/wcbrown/qepcad/INSTALL/IQ.html
- Website: (outdated) https://www.usna.edu/Users/cs/wcbrown/qepcad/B/QEPCAD.html


Type
----

optional


Dependencies
------------



Version Information
-------------------

package-version.txt::

    2.2.8

See https://repology.org/project/saclib/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i saclib

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libsaclib-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install saclib saclib-devel


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
