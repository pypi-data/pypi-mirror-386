.. _spkg_acsv:

acsv: Algorithms for analytic combinatorics in several variables
================================================================

Description
-----------

SageMath package with algorithms for analytic combinatorics in several variables

License
-------

MIT License

Upstream Contact
----------------

- https://pypi.org/project/sage-acsv/
- https://github.com/passagemath/passagemath-pkg-acsv


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_graphs`
- :ref:`spkg_sagemath_polyhedra`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_singular`
- :ref:`spkg_sagemath_symbolics`

Version Information
-------------------

requirements.txt::

    sage-acsv @ git+https://github.com/passagemath/passagemath-pkg-acsv.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install sage-acsv@git+https://github.com/passagemath/passagemath-pkg-acsv.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i acsv


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
