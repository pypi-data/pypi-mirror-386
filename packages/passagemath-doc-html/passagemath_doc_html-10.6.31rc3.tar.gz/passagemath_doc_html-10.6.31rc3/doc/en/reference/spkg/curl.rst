.. _spkg_curl:

curl: Multiprotocol data transfer library and utility
=====================================================

Description
-----------

Multiprotocols data transfer library (and utility).

License
-------

"MIT style license" : see file "COPYING" at the root of the source
tarball, explanations at https://curl.haxx.se/docs/copyright.html.


Upstream Contact
----------------

According to the file README at the root of the tarball, contact is done
by mailing https://curl.haxx.se/mail/


Type
----

standard


Dependencies
------------

- :ref:`spkg_openssl`

Version Information
-------------------

package-version.txt::

    8.16.0

See https://repology.org/project/curl/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i curl

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add curl

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install curl

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install curl libcurl4-openssl-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install libcurl-devel curl

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install ftp/curl

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install curl

.. tab:: MacPorts:

   No package needed

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S -curl

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install curl pkgconfig\(libcurl\)

.. tab:: Slackware:

   .. CODE-BLOCK:: bash

       $ sudo slackpkg install curl cyrus-sasl openldap-client libssh2

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install curl libcurl-devel


If the system package is installed, ``./configure`` will check if it can be used.
