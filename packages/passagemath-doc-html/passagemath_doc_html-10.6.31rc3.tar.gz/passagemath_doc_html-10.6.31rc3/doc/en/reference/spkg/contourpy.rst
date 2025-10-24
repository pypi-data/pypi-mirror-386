.. _spkg_contourpy:

contourpy: Python library for calculating contours of 2D quadrilateral grids
============================================================================

Description
-----------

Python library for calculating contours of 2D quadrilateral grids

License
-------

BSD-3-Clause

Upstream Contact
----------------

https://pypi.org/project/contourpy/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_meson_python`
- :ref:`spkg_numpy`
- :ref:`spkg_pybind11`

Version Information
-------------------

package-version.txt::

    1.3.1

version_requirements.txt::

    contourpy

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install contourpy

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i contourpy

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-contourpy

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/contourpy


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
