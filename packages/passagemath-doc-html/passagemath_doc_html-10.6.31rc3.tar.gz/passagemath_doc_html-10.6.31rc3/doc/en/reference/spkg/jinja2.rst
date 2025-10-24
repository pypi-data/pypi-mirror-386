.. _spkg_jinja2:

jinja2: General purpose template engine for Python
==================================================

Description
-----------

Jinja2 is a library for Python 2.4 and onwards that is designed to be
flexible, fast and secure.

If you have any exposure to other text-based template languages, such as
Smarty or Django, you should feel right at home with Jinja2. It's both
designer and developer friendly by sticking to Python's principles and
adding functionality useful for templating environments.

License
-------

BSD-3-Clause

Upstream Contact
----------------

https://pypi.org/project/Jinja2/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_markupsafe`
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    3.1.6

src/pyproject.toml::

    jinja2

version_requirements.txt::

    jinja2 >=3.0

See https://repology.org/project/python:jinja2/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install jinja2

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i jinja2

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install jinja2

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-jinja2

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-jinja2

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/jinja

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-jinja2

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-jinja2

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-Jinja2


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
