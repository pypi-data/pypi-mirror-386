.. _spkg_bleach:

bleach: An HTML-sanitizing tool
===============================

Description
-----------

An easy safelist-based HTML-sanitizing tool.

License
-------

Apache License v2


Upstream Contact
----------------

Home Page: https://github.com/mozilla/bleach


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_pip`
- :ref:`spkg_six`
- :ref:`spkg_webencodings`

Version Information
-------------------

package-version.txt::

    6.1.0

version_requirements.txt::

    bleach >= 5

See https://repology.org/project/python:bleach/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install bleach\>=5

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i bleach

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-bleach

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install bleach

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-bleach

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-bleach

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/bleach

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-bleach

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-bleach

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-bleach


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
