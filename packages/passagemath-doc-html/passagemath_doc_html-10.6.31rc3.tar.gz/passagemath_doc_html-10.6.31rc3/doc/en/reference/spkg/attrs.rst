.. _spkg_attrs:

attrs: Decorator for Python classes with attributes
===================================================

Description
-----------

attrs is the Python package that will bring back the joy of writing classes
by relieving you from the drudgery of implementing object protocols
(aka dunder methods).

License
-------

MIT License


Upstream Contact
----------------

Home page: https://www.attrs.org


Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_importlib_metadata`
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    25.3.0

version_requirements.txt::

    attrs >=19.3.0

See https://repology.org/project/python:attrs/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install attrs\>=19.3.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i attrs

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install attrs

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/attrs

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-attrs

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-attrs


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
