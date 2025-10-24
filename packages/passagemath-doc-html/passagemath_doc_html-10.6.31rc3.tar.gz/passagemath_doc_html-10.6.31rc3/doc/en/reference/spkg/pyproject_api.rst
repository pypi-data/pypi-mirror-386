.. _spkg_pyproject_api:

pyproject_api: API to interact with the python pyproject.toml based projects
============================================================================

Description
-----------

API to interact with the python pyproject.toml based projects

License
-------

Upstream Contact
----------------

https://pypi.org/project/pyproject-api/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_pip`
- :ref:`spkg_tomli`

Version Information
-------------------

package-version.txt::

    1.9.1

version_requirements.txt::

    pyproject-api

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pyproject-api

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pyproject_api

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-pyproject-api

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-pyproject-api

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-pyproject-api

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/pyproject-api

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-pyproject-api


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
