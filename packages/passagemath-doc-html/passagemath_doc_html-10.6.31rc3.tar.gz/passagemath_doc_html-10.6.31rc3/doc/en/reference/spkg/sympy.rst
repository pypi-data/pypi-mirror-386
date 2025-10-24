.. _spkg_sympy:

sympy: Python library for symbolic mathematics
==============================================

Description
-----------

SymPy is a Python library for symbolic mathematics. It aims to become a
full-featured computer algebra system (CAS) while keeping the code as
simple as possible in order to be comprehensible and easily extensible.
SymPy is written entirely in Python and does not require any external
libraries, except optionally for plotting support.

Website
-------

https://sympy.org/

License
-------

New BSD: http://www.opensource.org/licenses/bsd-license.php


Upstream Contact
----------------

https://pypi.org/project/sympy/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_mpmath`
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    1.14.0

src/pyproject.toml::

    sympy >=1.6, <2.0

version_requirements.txt::

    sympy

See https://repology.org/project/python:sympy/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install sympy\>=1.6\,\<2.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sympy

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-sympy

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install sympy

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-sympy

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-sympy

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/sympy

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-sympy

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-sympy

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-sympy


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
