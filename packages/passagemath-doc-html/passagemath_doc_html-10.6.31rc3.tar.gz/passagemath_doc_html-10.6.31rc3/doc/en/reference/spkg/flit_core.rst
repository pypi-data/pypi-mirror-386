.. _spkg_flit_core:

flit_core: Distribution-building parts of Flit. See flit package for more information
=====================================================================================

Description
-----------

Distribution-building parts of Flit. See flit package for more information

License
-------

Upstream Contact
----------------

https://pypi.org/project/flit-core/



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

    3.12.0

version_requirements.txt::

    flit-core >= 3.7.1

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install flit-core\>=3.7.1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i flit_core

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install flit-core

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-flit-core

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/flit_core

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-flit_core


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
