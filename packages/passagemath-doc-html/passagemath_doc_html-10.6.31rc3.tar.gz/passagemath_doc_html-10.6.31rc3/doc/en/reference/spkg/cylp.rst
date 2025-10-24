.. _spkg_cylp:

cylp: Python interface for CLP, CBC, and CGL
============================================

Description
-----------

Python interface for CLP, CBC, and CGL

License
-------

Eclipse Public License (EPL) version 2 (without a Secondary Licenses Notice).

Note: This license is incompatible with the GPL according to
https://www.gnu.org/licenses/license-list.html#EPL2;
see also the discussion in :issue:`26511`.

Upstream Contact
----------------

https://pypi.org/project/cylp/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_cbc`
- :ref:`spkg_numpy`
- :ref:`spkg_pip`
- :ref:`spkg_scipy`

Version Information
-------------------

package-version.txt::

    0.92.3

version_requirements.txt::

    cylp

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install cylp

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i cylp


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
