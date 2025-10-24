.. _spkg_pyproject_metadata:

pyproject_metadata: PEP 621 metadata parsing
============================================

Description
-----------

PEP 621 metadata parsing

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/pyproject-metadata/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_packaging`
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    0.9.1

version_requirements.txt::

    pyproject-metadata

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pyproject-metadata

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pyproject_metadata

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-pyproject-metadata

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install pyproject-metadata

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-pyproject-metadata

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-pyproject-metadata

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/pyproject-metadata

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-pyproject-metadata


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
