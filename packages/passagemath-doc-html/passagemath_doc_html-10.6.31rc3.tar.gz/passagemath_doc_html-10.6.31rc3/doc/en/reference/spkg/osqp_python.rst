.. _spkg_osqp_python:

osqp_python: The Operator Splitting QP Solver (Python wrapper)
==============================================================

Description
-----------

This is the Python wrapper for OSQP: The Operator Splitting QP Solver.

It vendors OSQP.

License
-------

Apache 2.0

Upstream Contact
----------------

https://pypi.org/project/osqp/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cmake`
- :ref:`spkg_numpy`
- :ref:`spkg_qdldl_python`
- :ref:`spkg_scipy`

Version Information
-------------------

package-version.txt::

    0.6.7.post3

version_requirements.txt::

    osqp

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install osqp

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i osqp_python

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install osqp


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
