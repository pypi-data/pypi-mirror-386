.. _spkg_sbcl:

sbcl: a lisp compiler and runtime system
=====================================================================

Description
-----------

Steel Bank Common Lisp (SBCL) is a high performance Common Lisp compiler. It is
open source / free software, with a permissive license (see https://www.sbcl.org/history.html).
In addition to the compiler and runtime system for ANSI Common Lisp, it provides an interactive
environment including a debugger, a statistical profiler, a code coverage tool,
and many other extensions.

(taken from https://www.sbcl.org)

License
-------

- a mix of BSD-style and public domain


Upstream Contact
----------------

-  https://www.sbcl.org


Type
----

optional


Dependencies
------------



Version Information
-------------------

See https://repology.org/project/sbcl/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   This is a dummy package and cannot be installed using the Sage distribution.

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add sbcl

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S sbcl

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install sbcl

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install sbcl

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install sbcl

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install lang/sbcl

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-lisp/sbcl

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install sbcl

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install sbcl

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr sbcl

.. tab:: OpenBSD:

   install the following packages: lang/sbcl

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install sbcl

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install sbcl


If the system package is installed, ``./configure`` will check if it can be used.
