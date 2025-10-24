.. _spkg_rpy2:

rpy2: Python interface to R
===========================

Description
-----------

rpy2 is a redesign and rewrite of rpy. It is providing a low-level
interface to R, a proposed high-level interface, including wrappers to
graphical libraries, as well as R-like structures and functions.

License
-------

-  GPL 2+

Upstream Contact
----------------

- https://github.com/rpy2/rpy2

Special Installation Instructions
---------------------------------

In the Sage distribution, ``rpy2`` is a "semi-standard" package: It will be
automatically installed by the Sage distribution if a suitable system
installation of R is detected by ``configure``. (Note that Sage no longer
ships and installs its own copy of R.)


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cffi`
- :ref:`spkg_jinja2`
- :ref:`spkg_pycparser`
- :ref:`spkg_pytz`
- :ref:`spkg_tzlocal`

Version Information
-------------------

package-version.txt::

    3.4.5

src/pyproject.toml::

    rpy2 >=3.3

version_requirements.txt::

    rpy2

See https://repology.org/project/rpy2/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install rpy2\>=3.3

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i rpy2

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-rpy2

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install rpy2 r-lattice

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-rpy2

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install math/py-rpy2

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-rpy2

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-rpy2


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
