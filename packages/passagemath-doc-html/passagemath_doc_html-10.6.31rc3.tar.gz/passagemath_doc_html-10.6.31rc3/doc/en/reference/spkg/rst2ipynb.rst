.. _spkg_rst2ipynb:

rst2ipynb: Convert reStructuredText files to Jupyter notebooks
==============================================================

Description
-----------

The rst2pynb program converts a standalone reStructuredText file to a
Jupyter notebook file.

This is currently achieved by converting to markdown with pandoc and
then to Jupyter notebook using notedown, plus some configuration and
tweaks.

License
-------

BSD 3-Clause License


Upstream Contact
----------------

Authors: Scott Sievert and Nicolas M. Thiéry Home page:
https://github.com/nthiery/rst-to-ipynb

Special Update/Build Instructions
---------------------------------

Fetch tarball from https://pypi.python.org/pypi/rst2ipynb/

As it is written in Haskell, pandoc must be installed from the distro.

The main rationale for having a notedown package in Sage (rather than
just let pip fetch it) is that the version on pipy (1.5.0, 2015-10-07)
is outdated and lacks important features / fixes for us.


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_notedown`
- :ref:`spkg_pandoc`

Version Information
-------------------

package-version.txt::

    0.2.3

version_requirements.txt::

    rst2ipynb >=0.2.2

See https://repology.org/project/python:rst2ipynb/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install rst2ipynb\>=0.2.2

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i rst2ipynb


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
