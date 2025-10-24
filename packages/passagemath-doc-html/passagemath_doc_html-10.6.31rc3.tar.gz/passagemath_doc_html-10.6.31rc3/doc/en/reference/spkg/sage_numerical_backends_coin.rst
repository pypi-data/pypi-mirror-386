.. _spkg_sage_numerical_backends_coin:

sage_numerical_backends_coin: COIN-OR backend for Sage MixedIntegerLinearProgram
================================================================================

Description
-----------

COIN-OR backend for Sage MixedIntegerLinearProgram

License
-------

GPLv2+

Upstream Contact
----------------

https://pypi.org/project/passagemath-coin-or-cbc



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- $(SAGERUNTIME)
- :ref:`spkg_cbc`
- :ref:`spkg_cysignals`
- :ref:`spkg_cython`
- :ref:`spkg_ipywidgets`

Version Information
-------------------

package-version.txt::

    10.4.1

version_requirements.txt::

    passagemath-coin-or-cbc

See https://repology.org/project/sage-numerical-backends-coin/versions, https://repology.org/project/python:sage-numerical-backends-coin/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-coin-or-cbc

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sage_numerical_backends_coin


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
