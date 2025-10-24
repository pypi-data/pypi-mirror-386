.. _spkg_mathics:

mathics: General-purpose computer algebra system
================================================

Description
-----------

General-purpose computer algebra system

License
-------

GPL

Upstream Contact
----------------

https://pypi.org/project/Mathics3/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_charset_normalizer`
- :ref:`spkg_dateutil`
- :ref:`spkg_mpmath`
- :ref:`spkg_numpy`
- :ref:`spkg_pillow`
- :ref:`spkg_pyyaml`
- :ref:`spkg_requests`
- :ref:`spkg_sympy`
- :ref:`spkg_typing_extensions`

Version Information
-------------------

requirements.txt::

    Mathics3 @ git+https://github.com/Mathics3/mathics-core
    mathics-scanner @ git+https://github.com/Mathics3/mathics-scanner
    -c ${SAGE_VENV}/var/lib/sage/scripts/numpy/spkg-requirements.txt

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install Mathics3@git+https://github.com/Mathics3/mathics-core mathics-scanner@git+https://github.com/Mathics3/mathics-scanner -c\$\{SAGE_VENV\}/var/lib/sage/scripts/numpy/spkg-requirements.txt

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i mathics

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install mathics3


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
