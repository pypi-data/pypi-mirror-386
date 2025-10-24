.. _spkg_jedi:

jedi: Static analysis tool providing IDE support for Python
===========================================================

Description
-----------

Jedi is a static analysis tool for Python that is typically used in
IDEs/editors plugins. Jedi has a focus on autocompletion and goto
functionality. Other features include refactoring, code search and
finding references.


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_parso`

Version Information
-------------------

package-version.txt::

    0.19.2

version_requirements.txt::

    jedi >=0.17.0

See https://repology.org/project/jedi/versions, https://repology.org/project/python:jedi/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install jedi\>=0.17.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i jedi

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install jedi

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-jedi

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/jedi

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-jedi

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-jedi


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
