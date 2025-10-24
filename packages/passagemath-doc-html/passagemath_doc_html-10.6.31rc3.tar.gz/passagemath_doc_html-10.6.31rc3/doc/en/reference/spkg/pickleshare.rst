.. _spkg_pickleshare:

pickleshare: A 'shelve' like datastore with concurrency support
===============================================================

Description
-----------

PickleShare - a small 'shelve' like datastore with concurrency support

Like shelve, a PickleShareDB object acts like a normal dictionary.
Unlike shelve, many processes can access the database simultaneously.
Changing a value in database is immediately visible to other processes
accessing the same database.

Concurrency is possible because the values are stored in separate files.
Hence the "database" is a directory where all files are governed by
PickleShare.


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

    0.7.5

version_requirements.txt::

    pickleshare >=0.7.5

See https://repology.org/project/pickleshare/versions, https://repology.org/project/python:pickleshare/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pickleshare\>=0.7.5

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pickleshare

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-pickleshare

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install pickleshare

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-pickleshare

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-pickleshare

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/pickleshare

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-pickleshare

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-pickleshare

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-pickleshare


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
