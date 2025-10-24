.. _spkg_trove_classifiers:

trove_classifiers: Canonical source for classifiers on PyPI (pypi.org)
======================================================================

Description
-----------

Canonical source for classifiers on PyPI (pypi.org)

License
-------

Upstream Contact
----------------

https://pypi.org/project/trove-classifiers/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_calver`
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    2025.9.11.17

version_requirements.txt::

    trove-classifiers >= 2025.2

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install trove-classifiers\>=2025.2

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i trove_classifiers

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add py3-trove-classifiers

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-trove-classifiers

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-trove-classifiers

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install devel/py-trove-classifiers

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/trove-classifiers

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-trove-classifiers


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
