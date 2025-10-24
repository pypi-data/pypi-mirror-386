.. _spkg_pandocfilters:

pandocfilters: A Python module for writing pandoc filters
=========================================================

Description
-----------

A python module for writing pandoc filters.

License
-------

BSD 3-Clause License


Upstream Contact
----------------

Author: John MacFarlane Home page: https://github.com/jgm/pandocfilters

Special Update/Build Instructions
---------------------------------

Download the last release from
https://pypi.python.org/pypi/pandocfilters


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

    1.5.0

version_requirements.txt::

    pandocfilters >=1.4.2

See https://repology.org/project/python:pandocfilters/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pandocfilters\>=1.4.2

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pandocfilters

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-pandocfilters

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install pandocfilters

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-pandocfilters

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-pandocfilters

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/pandocfilters

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-pandocfilters

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python3-pandocfilters

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-pandocfilters


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
