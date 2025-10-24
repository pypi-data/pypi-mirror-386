.. _spkg_appdirs:

appdirs: Small Python module for determining appropriate platform-specific dirs, e.g. a "user data dir"
=======================================================================================================

Description
-----------

Small Python module for determining appropriate platform-specific dirs, e.g. a "user data dir"

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/appdirs/



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

    1.4.4

version_requirements.txt::

    appdirs

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install appdirs

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i appdirs

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install appdirs

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S -python-appdirs

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-appdirs


If the system package is installed, ``./configure`` will check if it can be used.
