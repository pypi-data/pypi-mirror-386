.. _spkg_gmpy2:

gmpy2: Python interface to GMP/MPIR, MPFR, and MPC
==================================================

Description
-----------

GMP/MPIR, MPFR, and MPC interface to Python

gmpy2 is a C-coded Python extension module that supports
multiple-precision arithmetic. In addition to supporting GMP or MPIR for
multiple-precision integer and rational arithmetic, gmpy2 adds support
for the MPFR (correctly rounded real floating-point arithmetic) and MPC
(correctly rounded complex floating-point arithmetic) libraries.

License
-------

LGPL-3.0+

Upstream Contact
----------------

https://pypi.org/project/gmpy2/


Type
----

standard


Dependencies
------------

- $(MP_LIBRARY)
- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_mpc`
- :ref:`spkg_mpfr`

Version Information
-------------------

package-version.txt::

    2.2.2a1

src/pyproject.toml::

    gmpy2 ~=2.1.b999

version_requirements.txt::

    gmpy2

See https://repology.org/project/python:gmpy2/versions, https://repology.org/project/python:gmpy2-devel/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install gmpy2~=2.1.b999

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i gmpy2

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-gmpy2

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install gmpy2

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-gmpy2

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-gmpy2

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/py-gmpy2

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/gmpy

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-gmpy2

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-gmpy2

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-gmpy2


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
