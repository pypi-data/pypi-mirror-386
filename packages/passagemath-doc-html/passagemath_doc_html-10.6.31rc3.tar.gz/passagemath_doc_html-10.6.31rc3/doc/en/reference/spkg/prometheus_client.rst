.. _spkg_prometheus_client:

prometheus_client: Python client for the systems monitoring and alerting toolkit Prometheus
===========================================================================================

Description
-----------

The official Python 2 and 3 client for Prometheus (see
https://prometheus.io), an open-source systems monitoring and alerting
toolkit.


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

    0.14.1

version_requirements.txt::

    prometheus_client >=0.8.0

See https://repology.org/project/python:prometheus-client/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install prometheus_client\>=0.8.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i prometheus_client

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install prometheus_client

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-prometheus_client

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/prometheus_client

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-prometheus_client

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-prometheus_client

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-prometheus_client


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
