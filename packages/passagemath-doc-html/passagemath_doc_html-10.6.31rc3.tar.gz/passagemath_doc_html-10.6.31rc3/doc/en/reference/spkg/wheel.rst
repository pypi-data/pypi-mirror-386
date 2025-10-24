.. _spkg_wheel:

wheel: A built-package format for Python
========================================

Description
-----------

A built-package format for Python

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/wheel/



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

    0.44.0

src/pyproject.toml::

    wheel >=0.36.2

version_requirements.txt::

    wheel

See https://repology.org/project/wheel/versions, https://repology.org/project/python:wheel/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install wheel\>=0.36.2

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i wheel

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-wheel

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install wheel

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-wheel

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-wheel

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/wheel

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-wheel

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-wheel

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-wheel


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
