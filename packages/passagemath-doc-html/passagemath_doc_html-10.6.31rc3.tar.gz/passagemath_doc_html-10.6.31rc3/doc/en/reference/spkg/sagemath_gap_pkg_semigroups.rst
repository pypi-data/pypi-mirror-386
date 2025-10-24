.. _spkg_sagemath_gap_pkg_semigroups:

==============================================================================================
sagemath_gap_pkg_semigroups: Computational Group Theory with GAP: semigroups package
==============================================================================================


This pip-installable distribution ``passagemath-gap-pkg-semigroups`` is a
distribution of the GAP package `semigroups <https://semigroups.github.io/Semigroups/>`__,
for use with ``passagemath-gap``.


What is included
----------------

- Wheels on PyPI include the GAP package ``semigroups``


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cython`
- :ref:`spkg_gap`
- :ref:`spkg_pkgconfig`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_semigroups`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.6.31.rc3

version_requirements.txt::

    passagemath-gap-pkg-semigroups == 10.6.31rc3

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-gap-pkg-semigroups==10.6.31rc3

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_gap_pkg_semigroups


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
