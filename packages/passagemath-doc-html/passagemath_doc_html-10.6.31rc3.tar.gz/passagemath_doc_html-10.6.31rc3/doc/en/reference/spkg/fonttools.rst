.. _spkg_fonttools:

fonttools: Tools to manipulate font files
=========================================

Description
-----------

Tools to manipulate font files

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/fonttools/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cython`

Version Information
-------------------

package-version.txt::

    4.60.1

version_requirements.txt::

    fonttools

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install fonttools

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i fonttools

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install fonttools

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-fonttools

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/fonttools


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
