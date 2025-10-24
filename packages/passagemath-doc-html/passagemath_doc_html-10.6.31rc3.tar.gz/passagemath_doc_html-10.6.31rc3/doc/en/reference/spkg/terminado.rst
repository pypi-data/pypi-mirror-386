.. _spkg_terminado:

terminado: Tornado websocket backend for the term.js Javascript terminal emulator library
=========================================================================================

Description
-----------

This is a Tornado websocket backend for the term.js Javascript terminal
emulator library.

It evolved out of pyxterm, which was part of GraphTerm (as lineterm.py),
v0.57.0 (2014-07-18), and ultimately derived from the public-domain
Ajaxterm code, v0.11 (2008-11-13) (also on Github as part of QWeb).


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_hatchling`
- :ref:`spkg_ptyprocess`
- :ref:`spkg_tornado`

Version Information
-------------------

package-version.txt::

    0.17.1

version_requirements.txt::

    terminado >=0.8.3

See https://repology.org/project/terminado/versions, https://repology.org/project/python:terminado/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install terminado\>=0.8.3

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i terminado

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install terminado

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/terminado

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-terminado

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-terminado


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
