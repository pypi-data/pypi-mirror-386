.. _spkg_ecos_python:

ecos_python: Embedded Cone Solver (Python wrapper)
==================================================

Description
-----------

This is the Python package for ECOS: Embedded Cone Solver.

It vendors ECOS.

License
-------

GPLv3

Upstream Contact
----------------

https://pypi.org/project/ecos/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_numpy`
- :ref:`spkg_scipy`

Version Information
-------------------

package-version.txt::

    2.0.14

version_requirements.txt::

    ecos

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install ecos

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i ecos_python

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install ecos


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
