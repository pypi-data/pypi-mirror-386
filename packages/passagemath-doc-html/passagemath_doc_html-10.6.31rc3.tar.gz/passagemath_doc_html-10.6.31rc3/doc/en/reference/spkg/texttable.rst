.. _spkg_texttable:

texttable: Python module for creating simple ASCII tables
=========================================================

Description
-----------

Python module for creating simple ASCII tables

License
-------

MIT License (MIT)


Upstream Contact
----------------

https://github.com/foutaise/texttable/

Dependencies
------------

-  python


Special Update/Build Instructions
---------------------------------


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)

Version Information
-------------------

package-version.txt::

    1.7.0

version_requirements.txt::

    texttable >=1.6.3

See https://repology.org/project/texttable/versions, https://repology.org/project/python:texttable/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install texttable\>=1.6.3

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i texttable

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-texttable

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install texttable

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-texttable

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-texttable

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/texttable

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-texttable

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-texttable

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-texttable


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
