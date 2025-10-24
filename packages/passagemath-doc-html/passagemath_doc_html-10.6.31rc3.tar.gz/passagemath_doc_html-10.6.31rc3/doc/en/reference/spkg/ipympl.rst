.. _spkg_ipympl:

ipympl: Matplotlib Jupyter Extension
====================================

Description
-----------

Matplotlib Jupyter Extension

License
-------

BSD License

Upstream Contact
----------------

https://pypi.org/project/ipympl/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_ipython`
- :ref:`spkg_ipython_genutils`
- :ref:`spkg_ipywidgets`
- :ref:`spkg_matplotlib`
- :ref:`spkg_numpy`
- :ref:`spkg_pillow`
- :ref:`spkg_pip`
- :ref:`spkg_traitlets`

Version Information
-------------------

package-version.txt::

    0.9.7

version_requirements.txt::

    ipympl

See https://repology.org/project/python:ipympl/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install ipympl

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i ipympl

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-ipympl

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install ipympl

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install devel/py-ipympl

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-ipympl


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
