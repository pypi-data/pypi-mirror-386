.. _spkg_polymake:

polymake: Computations with polyhedra, fans, simplicial complexes, matroids, graphs, tropical hypersurfaces
===========================================================================================================

Description
-----------

polymake is open source software for research in polyhedral geometry. It
deals with polytopes, polyhedra and fans as well as simplicial
complexes, matroids, graphs, tropical hypersurfaces, and other objects.
Supported platforms include various flavors of Linux, Free BSD and Mac
OS.

License
-------

-  GPL v3


Upstream Contact
----------------

-  https://polymake.org/

Dependencies
------------

Polymake needs a working installation of Perl, including its shared
library and some modules (``XML::Writer XML::LibXML XML::LibXSLT
Term::ReadLine::Gnu JSON SVG``). The Polymake interface in Sage
additionally needs ``File::Slurp``. For full functionality including
polymake's polyDB, also the Perl module ``MongoDB`` is needed.

These are not provided by a Sage package. The dummy package
``perl_cpan_polymake_prereq`` will signal an error at build time if the
required prerequisites are not met.

The ``configure`` script will inform you about the equivalent system
packages that you should install. Otherwise, you can use CPAN (see
below).

Sage might install the ``Term::ReadLine::Gnu`` module, however, when you
install polymake, if it is not provided by the system, or if Sage
installs its own ``readline`` library.


A distribution-independent way to install Perl modules (into a user's
home directory or ``/usr/local``) is using CPAN. This is also the way to
install the modules on macOS. For this, if you don't have root access,
you will need the ``local::lib`` Perl module installed::

   cpan -i XML::Writer XML::LibXML XML::LibXSLT File::Slurp Term::ReadLine::Gnu JSON SVG MongoDB

Before installing the ``polymake`` package, refer to the SPKG pages for the following packages to ensure a more featureful Polymake installation:

- [4ti2](https://passagemath.org/docs/latest/html/en/reference/spkg/4ti2.html)
- [latte_int](https://passagemath.org/docs/latest/html/en/reference/spkg/latte_int.html)
- [topcom](https://passagemath.org/docs/latest/html/en/reference/spkg/topcom.html)
- [qhull](https://passagemath.org/docs/latest/html/en/reference/spkg/qhull.html)

For additional software that may enhance your Polymake installation (but for which no Sage package is available), you can manually install the following:

- ``azove``
- ``porta``
- ``vinci``
- ``SplitsTree4``

Information on missing Polymake prerequisites after installing polymake::

   $ sage -sh
   (sage-sh) $ polymake
   polytope> show_unconfigured;

In order to use Polymake from Sage, please refer to the [Jupymake SPKG page](https://passagemath.org/docs/latest/html/en/reference/spkg/jupymake.html) for installation instructions.



Debugging polymake install problems
-----------------------------------

::

  # apt-get install libdevel-trace-perl
  $ cd src
  $ perl -d:Trace support/configure.pl


Type
----

optional


Dependencies
------------

- $(MP_LIBRARY)
- :ref:`spkg_bliss`
- :ref:`spkg_cddlib`
- :ref:`spkg_libxml2`
- :ref:`spkg_lrslib`
- :ref:`spkg_ninja_build`
- :ref:`spkg_normaliz`
- :ref:`spkg_perl_cpan_polymake_prereq`
- :ref:`spkg_perl_term_readline_gnu`
- :ref:`spkg_ppl`

Version Information
-------------------

package-version.txt::

    4.14

See https://repology.org/project/polymake/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i polymake

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S polymake

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install polymake libpolymake-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install polymake

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install apaffenholz/polymake/polymake

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr polymake

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install polymake


If the system package is installed, ``./configure`` will check if it can be used.
