.. _spkg_typing_extensions:

typing_extensions: Backported and Experimental Type Hints for Python 3.8+
=========================================================================

Description
-----------

Backported and Experimental Type Hints for Python 3.8+

License
-------

PSF

Upstream Contact
----------------

https://pypi.org/project/typing-extensions/



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

    4.13.2

src/pyproject.toml::

    typing_extensions >= 4.7.0; python_version<'3.13'

version_requirements.txt::

    typing_extensions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install typing_extensions\>=4.7.0\;python_version\<\"3.13\"

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i typing_extensions

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-typing_extensions

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install typing_extensions

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-typing-extensions

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-typing-extensions

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install devel/py-typing-extensions

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/typing-extensions

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-typing_extensions

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-typing_extensions


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
