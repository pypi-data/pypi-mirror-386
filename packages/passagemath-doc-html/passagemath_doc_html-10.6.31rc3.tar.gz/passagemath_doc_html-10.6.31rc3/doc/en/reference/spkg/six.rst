.. _spkg_six:

six: Python 2 and 3 compatibility utilities
===========================================

Description
-----------

Python 2 and 3 compatibility utilities

License
-------

MIT License


Upstream Contact
----------------

- Author: Benjamin Peterson
- Home page: http://pypi.python.org/pypi/six/

Dependencies
------------

Python


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

    1.17.0

src/pyproject.toml::

    six >=1.15.0

version_requirements.txt::

    six >=1.16.0

See https://repology.org/project/python:six/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install six\>=1.15.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i six

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-six

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install six

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-six

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-six

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/six

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-six

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-six

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-six


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
