.. _spkg_appnope:

appnope: Disable App Nap on macOS >= 10.9
=========================================

Description
-----------

Disable App Nap on macOS >= 10.9

License
-------

BSD

Upstream Contact
----------------

https://pypi.org/project/appnope/



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

    0.1.4

version_requirements.txt::

    appnope >=0.1.0

See https://repology.org/project/python:appnope/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install appnope\>=0.1.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i appnope

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install appnope

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-appnope


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
