.. _spkg_platformdirs:

platformdirs: Small Python package for determining appropriate platform-specific dirs, e.g. a "user data dir"
=============================================================================================================

Description
-----------

Small Python package for determining appropriate platform-specific dirs, e.g. a "user data dir"

License
-------

Upstream Contact
----------------

https://pypi.org/project/platformdirs/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    4.2.2

version_requirements.txt::

    platformdirs

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install platformdirs

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i platformdirs

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install platformdirs

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-platformdirs

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/platformdirs


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
