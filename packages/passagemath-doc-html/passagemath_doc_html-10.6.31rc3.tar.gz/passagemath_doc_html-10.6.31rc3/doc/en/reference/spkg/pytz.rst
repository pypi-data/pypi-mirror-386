.. _spkg_pytz:

pytz: Timezone definitions for Python
=====================================

Description
-----------

World Timezone Definitions for Python
See https://pypi.org/project/pytz/


Special Update/Build Instructions
---------------------------------

The upstream tarball was repackaged after sanitizing the file
permissions with

$ chmod go-w


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)

Version Information
-------------------

package-version.txt::

    2023.3.post1

version_requirements.txt::

    pytz >=2020.1

See https://repology.org/project/python:pytz/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pytz\>=2020.1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pytz

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-pytz

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install pytz

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-tz

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-pytz

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/pytz

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-tz

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-pytz

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-pytz


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
