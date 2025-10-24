.. _spkg_markupsafe:

markupsafe: Safely add untrusted strings to HTML/XML markup
===========================================================

Description
-----------

Implements a XML/HTML/XHTML Markup safe string for Python

License
-------

BSD-3-Clause

Upstream Contact
----------------

https://pypi.org/project/MarkupSafe/



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

    2.1.5

version_requirements.txt::

    markupsafe >=2.0

See https://repology.org/project/python:markupsafe/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install markupsafe\>=2.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i markupsafe

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install markupsafe

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-markupsafe

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/markupsafe

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-markupsafe

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-MarkupSafe

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-MarkupSafe


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
