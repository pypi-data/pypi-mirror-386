.. _spkg_qdldl_python:

qdldl_python: QDLDL, a free LDL factorization routine (Python wrapper)
======================================================================

Description
-----------

QDLDL, a free LDL factorization routine.

License
-------

Apache 2.0

Upstream Contact
----------------

https://pypi.org/project/qdldl/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cmake`
- :ref:`spkg_numpy`
- :ref:`spkg_pybind11`
- :ref:`spkg_scipy`

Version Information
-------------------

package-version.txt::

    0.1.5.post3

version_requirements.txt::

    qdldl

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install qdldl

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i qdldl_python

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install qdldl-python


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
