.. _spkg_sniffio:

sniffio: Sniff out which async library your code is running under
=================================================================

Description
-----------

Sniff out which async library your code is running under

License
-------

MIT OR Apache-2.0

Upstream Contact
----------------

https://pypi.org/project/sniffio/



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

    1.3.1

version_requirements.txt::

    sniffio

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install sniffio

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sniffio


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
