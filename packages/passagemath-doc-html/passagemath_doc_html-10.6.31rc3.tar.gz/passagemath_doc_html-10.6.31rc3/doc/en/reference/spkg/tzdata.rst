.. _spkg_tzdata:

tzdata: Provider of IANA time zone data
=======================================

Description
-----------

Provider of IANA time zone data

License
-------

Apache-2.0

Upstream Contact
----------------

https://pypi.org/project/tzdata/



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

    2023.3

version_requirements.txt::

    tzdata

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install tzdata

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i tzdata

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install python-tzdata

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install tzdata


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
