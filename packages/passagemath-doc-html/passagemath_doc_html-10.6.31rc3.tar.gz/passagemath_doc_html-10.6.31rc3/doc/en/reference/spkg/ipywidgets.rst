.. _spkg_ipywidgets:

ipywidgets: Interactive HTML widgets for Jupyter notebooks and the IPython kernel
=================================================================================

Description
-----------

Interactive HTML widgets for Jupyter notebooks and the IPython kernel.


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_comm`
- :ref:`spkg_ipykernel`
- :ref:`spkg_ipython`
- :ref:`spkg_jupyterlab_widgets`
- :ref:`spkg_traitlets`
- :ref:`spkg_widgetsnbextension`

Version Information
-------------------

package-version.txt::

    8.1.7

src/pyproject.toml::

    ipywidgets >=7.5.1

version_requirements.txt::

    ipywidgets

See https://repology.org/project/python:ipywidgets/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install ipywidgets\>=7.5.1

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i ipywidgets

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install ipywidgets\>=7.5.1

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-ipywidgets

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/ipywidgets

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install py-ipywidgets

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-jupyter_ipywidgets


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
