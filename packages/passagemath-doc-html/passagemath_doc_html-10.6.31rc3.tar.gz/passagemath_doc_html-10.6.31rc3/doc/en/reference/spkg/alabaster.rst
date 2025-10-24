.. _spkg_alabaster:

alabaster: Default theme for the Sphinx documentation system
============================================================

Description
-----------

Alabaster is a visually (c)lean, responsive, configurable theme for the
Sphinx documentation system. It is Python 2+3 compatible.

It began as a third-party theme, and is still maintained separately, but
as of Sphinx 1.3, Alabaster is an install-time dependency of Sphinx and
is selected as the default theme.

Live examples of this theme can be seen on paramiko.org, fabfile.org and
pyinvoke.org.

Upstream Contact
----------------

https://alabaster.readthedocs.io/en/latest/


Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    0.7.16

version_requirements.txt::

    alabaster >=0.7.12

See https://repology.org/project/alabaster/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install alabaster\>=0.7.12

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i alabaster

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install alabaster

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/alabaster

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-alabaster

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-alabaster


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
