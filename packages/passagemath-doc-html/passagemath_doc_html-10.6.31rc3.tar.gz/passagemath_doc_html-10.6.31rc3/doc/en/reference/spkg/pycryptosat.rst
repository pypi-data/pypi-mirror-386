.. _spkg_pycryptosat:

pycryptosat: Python module of cryptominisat
===========================================

Description
-----------

Build and install pycryptosat (Python frontend to CryptoMiniSat, which will be built if needed too).

CryptoMiniSat is a SAT solver that aims to become a premiere SAT solver
with all the features and speed of successful SAT solvers, such as MiniSat
and PrecoSat. The long-term goals of CryptoMiniSat are to be an efficient
sequential, parallel and distributed solver. There are solvers that are
good at one or the other, e.g. ManySat (parallel) or PSolver (distributed),
but we wish to excel at all.

CryptoMiniSat 2.5 won the SAT Race 2010 among 20 solvers submitted by researchers and industry.



License
-------

MIT License


Upstream Contact
----------------

-  Authors: Mate Soos
-  Email: soos.mate@gmail.com
-  Website: http://www.msoos.org/
-  Releases: https://github.com/msoos/cryptominisat/releases


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_boost_cropped`
- :ref:`spkg_cmake`
- :ref:`spkg_libpng`
- :ref:`spkg_m4ri`
- :ref:`spkg_zlib`

Version Information
-------------------

requirements.txt::

    pycryptosat

See https://repology.org/project/cryptominisat/versions

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pycryptosat

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pycryptosat

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install cryptominisat

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-pycryptosat

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install cryptominisat


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
