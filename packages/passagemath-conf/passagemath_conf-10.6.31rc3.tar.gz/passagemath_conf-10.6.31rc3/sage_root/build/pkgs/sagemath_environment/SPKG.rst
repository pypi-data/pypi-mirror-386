=========================================================================
 passagemath: System and software environment
=========================================================================

`passagemath <https://github.com/passagemath/passagemath>`__ is open
source mathematical software in Python, released under the GNU General
Public Licence GPLv2+.

It is a fork of `SageMath <https://www.sagemath.org/>`__, which has been
developed 2005-2025 under the motto “Creating a Viable Open Source
Alternative to Magma, Maple, Mathematica, and MATLAB”.

The passagemath fork uses the motto "Creating a Free Passage Between the
Scientific Python Ecosystem and Mathematical Software Communities."
It was created in October 2024 with the following goals:

-  providing modularized installation with pip,
-  establishing first-class membership in the scientific Python
   ecosystem,
-  giving `clear attribution of upstream
   projects <https://groups.google.com/g/sage-devel/c/6HO1HEtL1Fs/m/G002rPGpAAAJ>`__,
-  providing independently usable Python interfaces to upstream
   libraries,
-  offering `platform portability and integration testing
   services <https://github.com/passagemath/passagemath/issues/704>`__
   to upstream projects,
-  inviting collaborations with upstream projects,
-  `building a professional, respectful, inclusive
   community <https://groups.google.com/g/sage-devel/c/xBzaINHWwUQ>`__,
-  `empowering Sage users to participate in the scientific Python ecosystem
   <https://github.com/passagemath/passagemath/issues/248>`__ by publishing packages,
-  developing a port to `Pyodide <https://pyodide.org/en/stable/>`__ for
   serverless deployment with Javascript,
-  developing a native Windows port.

`Full documentation <https://passagemath.org/docs/latest/html/en/index.html>`__ is
available online.

passagemath attempts to support and provides binary wheels suitable for
all major Linux distributions and recent versions of macOS.

Binary wheels for native Windows (x86_64) are are available for a subset of
the passagemath distributions. Use of the full functionality of passagemath
on Windows currently requires the use of Windows Subsystem for Linux (WSL)
or virtualization.

The supported Python versions in the passagemath 10.6.x series are 3.10.x-3.13.x.


About this pip-installable distribution package
-----------------------------------------------

The pip-installable distribution package ``passagemath-environment`` is a
distribution of a small part of the Sage Library.

It provides a small, fundamental subset of the modules of the Sage
library ("sagelib", ``passagemath-standard``), providing the connection to the
system and software environment.


What is included
----------------

* ``sage`` script for launching the Sage REPL and accessing various developer tools
  (see ``sage --help``, `Invoking Sage <https://passagemath.org/docs/latest/html/en/reference/repl/options.html>`_).

* sage.env

* `sage.features <https://passagemath.org/docs/latest/html/en/reference/misc/sage/features.html>`_: Testing for features of the environment at runtime

* `sage.misc.package <https://passagemath.org/docs/latest/html/en/reference/misc/sage/misc/package.html>`_: Listing packages of the Sage distribution

* `sage.misc.package_dir <https://passagemath.org/docs/latest/html/en/reference/misc/sage/misc/package_dir.html>`_

* `sage.misc.temporary_file <https://passagemath.org/docs/latest/html/en/reference/misc/sage/misc/temporary_file.html>`_

* `sage.misc.viewer <https://passagemath.org/docs/latest/html/en/reference/misc/sage/misc/viewer.html>`_
