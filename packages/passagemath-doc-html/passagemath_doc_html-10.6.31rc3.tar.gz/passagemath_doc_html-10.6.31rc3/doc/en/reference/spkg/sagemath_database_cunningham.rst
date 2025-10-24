.. _spkg_sagemath_database_cunningham:

=================================================================================================
sagemath_database_cunningham: List of the prime numbers occuring in the Cunningham table
=================================================================================================


This pip-installable distribution ``passagemath-database-cunningham`` is a
distribution of the list of the prime numbers occuring in the Cunningham table.


What is included
----------------

- Wheels on PyPI include the cunningham_tables files


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cunningham_tables`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.6.31.rc3

version_requirements.txt::

    passagemath-database-cunningham == 10.6.31rc3

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-database-cunningham==10.6.31rc3

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_database_cunningham


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
