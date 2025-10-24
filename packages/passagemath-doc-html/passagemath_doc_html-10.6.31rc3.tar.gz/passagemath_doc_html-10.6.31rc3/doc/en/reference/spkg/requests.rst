.. _spkg_requests:

requests: An HTTP library for Python
====================================

Description
-----------

Python HTTP for Humans.

License
-------

Apache 2.0

Upstream Contact
----------------

https://pypi.org/project/requests/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_certifi`
- :ref:`spkg_charset_normalizer`
- :ref:`spkg_idna`
- :ref:`spkg_pip`
- :ref:`spkg_urllib3`

Version Information
-------------------

package-version.txt::

    2.32.4

src/pyproject.toml::

    requests >=2.13.0

version_requirements.txt::

    requests

See https://repology.org/project/requests/versions, https://repology.org/project/python:requests/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install requests\>=2.13.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i requests

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-requests

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install requests

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-requests

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-requests

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/requests

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-requests

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-requests

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-requests


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
