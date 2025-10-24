.. _spkg_importlib_metadata:

importlib_metadata: Library to access the metadata for a Python package
=======================================================================

Description
-----------

This is a backport package, supplying access to the functionality of
``importlib.metadata`` including improvements added to subsequent Python versions.


License
-------

Apache Software License


Upstream Contact
----------------

- https://pypi.org/project/importlib-metadata/

- http://importlib-metadata.readthedocs.io/


Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_pip`
- :ref:`spkg_tomli`
- :ref:`spkg_typing_extensions`
- :ref:`spkg_zipp`

Version Information
-------------------

package-version.txt::

    8.7.0

src/pyproject.toml::

    importlib_metadata >=6.5; python_version<'3.12'

version_requirements.txt::

    importlib_metadata

See https://repology.org/project/python:importlib-metadata/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install importlib_metadata\>=6.5\;python_version\<\"3.12\"

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i importlib_metadata

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-importlib-metadata

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install importlib_metadata

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-importlib-metadata

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-importlib-metadata

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install devel/py-importlib-metadata

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/importlib_metadata

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-importlib-metadata

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-importlib_metadata


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
