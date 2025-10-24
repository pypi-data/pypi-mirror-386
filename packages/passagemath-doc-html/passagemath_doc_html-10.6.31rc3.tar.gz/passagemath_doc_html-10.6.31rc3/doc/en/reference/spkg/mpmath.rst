.. _spkg_mpmath:

mpmath: Pure Python library for multiprecision floating-point arithmetic
========================================================================

Description
-----------

Mpmath is a pure-Python library for multiprecision floating-point
arithmetic. It provides an extensive set of transcendental functions,
unlimited exponent sizes, complex numbers, interval arithmetic,
numerical integration and differentiation, root-finding, linear algebra,
and much more. Almost any calculation can be performed just as well at
10-digit or 1000-digit precision, and in many cases mpmath implements
asymptotically fast algorithms that scale well for extremely high
precision work. If available, mpmath will (optionally) use gmpy to speed
up high precision operations.


Upstream Contact
----------------

-  Author: Fredrik Johansson
-  Email: fredrik.johansson@gmail.com
-  https://mpmath.org
-  Website: https://github.com/mpmath/mpmath



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)

Version Information
-------------------

package-version.txt::

    1.3.0

src/pyproject.toml::

    mpmath >=1.1.0, <1.4

version_requirements.txt::

    mpmath

See https://repology.org/project/mpmath/versions, https://repology.org/project/python:mpmath/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install mpmath\>=1.1.0\,\<1.4

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i mpmath

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-mpmath

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install mpmath

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-mpmath

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-mpmath

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/mpmath

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-mpmath

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-mpmath


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
