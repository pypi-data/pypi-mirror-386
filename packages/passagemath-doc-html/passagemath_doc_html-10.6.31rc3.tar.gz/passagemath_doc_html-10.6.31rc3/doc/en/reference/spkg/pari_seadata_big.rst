.. _spkg_pari_seadata_big:

pari_seadata_big: PARI data package needed by ellap for large primes (big version)
==================================================================================

Description
-----------

Needed by ellap for large primes. These polynomials were extracted from
the ECHIDNA databases and computed by David R. Kohel.
This contains extra modular polynomials of level between 500 and 800.
This is suitable for fields up to 1100 bits.
PARI/GP 2.9 contains fallback
code to go on when all modular polynomials in the database have been
exhausted and can handle larger fields (with an important slowdown).

License
-------

GNU General Public License (GPL version 2 or any later version).


Upstream Contact
----------------

http://pari.math.u-bordeaux.fr/


Type
----

optional


Dependencies
------------



Version Information
-------------------

package-version.txt::

    20170418

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pari_seadata_big


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
