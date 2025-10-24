.. _spkg_valgrind:

valgrind: Memory error detector, call graph generator, runtime profiler
=======================================================================

Description
-----------

Valgrind is an instrumentation framework for building dynamic analysis
tools. There are Valgrind tools that can automatically detect many
memory management and threading bugs, and profile your programs in
detail. You can also use Valgrind to build new tools.

The Valgrind distribution currently includes six production-quality
tools: a memory error detector, two thread error detectors, a cache and
branch-prediction profiler, a call-graph generating cache and
branch-prediction profiler, and a heap profiler. It also includes three
experimental tools: a heap/stack/global array overrun detector, a second
heap profiler that examines how heap blocks are used, and a SimPoint
basic block vector generator.

License
-------

Valgrind is Open Source / Free Software, and is freely available under
the GNU General Public License, version 2.


Upstream Contact
----------------

-  http://www.valgrind.org/
-  valgrind-user, valgrind-devel mailing lists


Type
----

optional


Dependencies
------------



Version Information
-------------------

See https://repology.org/project/valgrind/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   This is a dummy package and cannot be installed using the Sage distribution.

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add valgrind

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install valgrind

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install valgrind vagrind-devel

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install valgrind

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install valgrind

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install valgrind

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install valgrind


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
