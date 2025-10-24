.. _spkg_meson:

meson: A high performance build system
======================================

Description
-----------

A high performance build system

License
-------

Apache License, Version 2.0

Upstream Contact
----------------

https://pypi.org/project/meson/



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

    1.9.1

version_requirements.txt::

    meson >= 1.5.0

See https://repology.org/project/meson/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install meson\>=1.5.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i meson

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add meson

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S meson

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install meson

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install meson

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install meson

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install devel/meson

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-build/meson

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install meson

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr meson

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install meson

.. tab:: Slackware:

   .. CODE-BLOCK:: bash

       $ sudo slackpkg install meson


If the system package is installed, ``./configure`` will check if it can be used.
