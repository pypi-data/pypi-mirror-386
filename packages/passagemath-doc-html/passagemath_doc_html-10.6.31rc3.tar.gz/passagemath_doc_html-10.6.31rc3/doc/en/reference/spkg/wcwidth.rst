.. _spkg_wcwidth:

wcwidth: Measures the displayed width of unicode strings in a terminal
======================================================================

Description
-----------

Measures the displayed width of unicode strings in a terminal

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/wcwidth/



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

    0.2.13

version_requirements.txt::

    wcwidth >=0.1.7

See https://repology.org/project/wcwidth/versions, https://repology.org/project/python:wcwidth/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install wcwidth\>=0.1.7

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i wcwidth

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install wcwidth

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-wcwidth

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/wcwidth

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-wcwidth

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-wcwidth

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-wcwidth


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
