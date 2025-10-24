.. _spkg_imagesize:

imagesize: Getting image size from png/jpeg/jpeg2000/gif file
=============================================================

Description
-----------

Getting image size from png/jpeg/jpeg2000/gif file

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/imagesize/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    1.4.1

version_requirements.txt::

    imagesize

See https://repology.org/project/python:imagesize/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install imagesize

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i imagesize

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install imagesize

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-imagesize

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/imagesize

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-imagesize

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-imagesize


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
