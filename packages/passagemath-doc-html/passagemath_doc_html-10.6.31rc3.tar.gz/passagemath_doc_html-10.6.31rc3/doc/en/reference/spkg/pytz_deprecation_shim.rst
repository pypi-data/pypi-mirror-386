.. _spkg_pytz_deprecation_shim:

pytz_deprecation_shim: Shims to make deprecation of pytz easier
===============================================================

Description
-----------

Shims to make deprecation of pytz easier

License
-------

Apache-2.0

Upstream Contact
----------------

https://pypi.org/project/pytz-deprecation-shim/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_tzdata`

Version Information
-------------------

package-version.txt::

    0.1.0.post0

version_requirements.txt::

    pytz-deprecation-shim

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pytz-deprecation-shim

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pytz_deprecation_shim

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install pytz-deprecation-shim

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-pytz-deprecation-shim


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
