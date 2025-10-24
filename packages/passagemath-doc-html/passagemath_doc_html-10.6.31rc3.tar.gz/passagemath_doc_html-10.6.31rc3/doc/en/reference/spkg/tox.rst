.. _spkg_tox:

tox: tox is a generic virtualenv management and test command line tool
======================================================================

Description
-----------

tox is a generic virtualenv management and test command line tool

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/tox/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cachetools`
- :ref:`spkg_chardet`
- :ref:`spkg_colorama`
- :ref:`spkg_filelock`
- :ref:`spkg_packaging`
- :ref:`spkg_pip`
- :ref:`spkg_platformdirs`
- :ref:`spkg_pluggy`
- :ref:`spkg_pyproject_api`
- :ref:`spkg_tomli`
- :ref:`spkg_virtualenv`

Version Information
-------------------

package-version.txt::

    4.11.1

version_requirements.txt::

    tox >= 4.11

See https://repology.org/project/python:tox/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install tox\>=4.11

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i tox

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-tox

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install tox

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install tox

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install tox

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install tox

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/tox

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install tox

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-tox

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S -python-tox

.. tab:: Slackware:

   .. CODE-BLOCK:: bash

       $ sudo slackpkg install tox

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install tox


If the system package is installed, ``./configure`` will check if it can be used.
