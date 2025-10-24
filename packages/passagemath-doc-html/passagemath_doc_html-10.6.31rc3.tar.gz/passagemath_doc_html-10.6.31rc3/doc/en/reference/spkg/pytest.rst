.. _spkg_pytest:

pytest: Simple powerful testing with Python
===========================================

Description
-----------

Simple powerful testing with Python

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/pytest/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_colorama`
- :ref:`spkg_exceptiongroup`
- :ref:`spkg_iniconfig`
- :ref:`spkg_packaging`
- :ref:`spkg_pip`
- :ref:`spkg_pluggy`
- :ref:`spkg_tomli`

Version Information
-------------------

package-version.txt::

    8.3.2

version_requirements.txt::

    pytest

See https://repology.org/project/python:pytest/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pytest

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pytest

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install pytest

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-pytest

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-pytest

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-pytest


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
