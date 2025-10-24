.. _spkg_mcqd:

mcqd: An exact algorithm for finding a maximum clique in an undirected graph
============================================================================

Description
-----------

MaxCliqueDyn is a fast exact algorithm for finding a maximum clique in
an undirected graph.

License
-------

GPL 3


Upstream Contact
----------------

MCQD is currently being maintained by Janez Konc.
https://gitlab.com/janezkonc/mcqd



Type
----

optional


Dependencies
------------



Version Information
-------------------

package-version.txt::

    1.0.p0

See https://repology.org/project/mcqd/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i mcqd

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S mcqd

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install mcqd mcqd-devel

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install mcqd


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
