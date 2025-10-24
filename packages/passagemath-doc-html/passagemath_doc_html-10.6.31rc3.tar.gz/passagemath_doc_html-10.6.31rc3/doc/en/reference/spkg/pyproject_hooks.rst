.. _spkg_pyproject_hooks:

pyproject_hooks: Wrappers to call pyproject.toml-based build backend hooks.
===========================================================================

Description
-----------

Wrappers to call pyproject.toml-based build backend hooks.

License
-------

Upstream Contact
----------------

https://pypi.org/project/pyproject_hooks/



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

    1.2.0

version_requirements.txt::

    pyproject_hooks

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pyproject_hooks

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pyproject_hooks

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-pyproject-hooks

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-pyproject-hooks

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-pyproject-hooks

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/pyproject-hooks

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-pyproject-hooks


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
