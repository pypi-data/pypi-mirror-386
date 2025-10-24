.. _spkg_fqdn:

fqdn: Validates fully-qualified domain names against RFC 1123, so that they are acceptable to modern bowsers
============================================================================================================

Description
-----------

Validates fully-qualified domain names against RFC 1123, so that they are acceptable to modern bowsers

License
-------

MPL 2.0

Upstream Contact
----------------

https://pypi.org/project/fqdn/



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

    1.5.1

version_requirements.txt::

    fqdn

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install fqdn

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i fqdn


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
