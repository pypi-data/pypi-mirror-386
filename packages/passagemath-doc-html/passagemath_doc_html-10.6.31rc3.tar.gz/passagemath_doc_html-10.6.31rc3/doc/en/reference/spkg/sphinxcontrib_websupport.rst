.. _spkg_sphinxcontrib_websupport:

sphinxcontrib_websupport: Sphinx API for Web apps
=================================================

Description
-----------

sphinxcontrib-websupport provides a Python API to easily integrate
Sphinx documentation into your Web application.

License
-------

BSD


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_pip`
- :ref:`spkg_sphinxcontrib_serializinghtml`

Version Information
-------------------

package-version.txt::

    2.0.0

version_requirements.txt::

    sphinxcontrib_websupport >=1.2.1

See https://repology.org/project/python:sphinxcontrib-websupport/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install sphinxcontrib_websupport\>=1.2.1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sphinxcontrib_websupport

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add py3-sphinxcontrib-websupport

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-sphinxcontrib-websupport

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install sphinxcontrib-websupport

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-sphinxcontrib.websupport

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-sphinxcontrib-websupport

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install textproc/py-sphinxcontrib-websupport

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/sphinxcontrib-websupport

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-sphinxcontrib-websupport

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-sphinxcontrib-websupport


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
