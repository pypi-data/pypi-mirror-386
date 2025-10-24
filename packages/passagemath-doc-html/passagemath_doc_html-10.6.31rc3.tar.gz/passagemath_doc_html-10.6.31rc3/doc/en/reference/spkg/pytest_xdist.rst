.. _spkg_pytest_xdist:

pytest_xdist: Pytest xdist plugin for distributed testing, most importantly across multiple CPUs
================================================================================================

Description
-----------

Pytest xdist plugin for distributed testing, most importantly across multiple CPUs

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/pytest-xdist/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_execnet`
- :ref:`spkg_pip`
- :ref:`spkg_pytest`

Version Information
-------------------

package-version.txt::

    3.6.1

version_requirements.txt::

    pytest-xdist

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pytest-xdist

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pytest_xdist

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install pytest-xdist

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-pytest-xdist


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
