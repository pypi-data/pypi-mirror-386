.. _spkg_gast:

gast: Python AST that abstracts the underlying Python version
=============================================================

Description
-----------

Python AST that abstracts the underlying Python version

License
-------

BSD 3-Clause

Upstream Contact
----------------

https://pypi.org/project/gast/



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

    0.6.0

version_requirements.txt::

    gast

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install gast

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i gast

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install gast

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-gast

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/gast

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-gast


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
