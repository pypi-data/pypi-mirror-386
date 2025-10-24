.. _spkg_virtualenv:

virtualenv: Virtual Python Environment builder
==============================================

Description
-----------

Virtual Python Environment builder

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/virtualenv/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_distlib`
- :ref:`spkg_filelock`
- :ref:`spkg_importlib_metadata`
- :ref:`spkg_pip`
- :ref:`spkg_platformdirs`

Version Information
-------------------

package-version.txt::

    20.26.2

version_requirements.txt::

    virtualenv

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install virtualenv

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i virtualenv

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install virtualenv

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-virtualenv

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S -python-virtualenv

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-virtualenv


If the system package is installed, ``./configure`` will check if it can be used.
