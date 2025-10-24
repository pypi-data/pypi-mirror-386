================================================================================================================
 passagemath: Computer algebra, algebraic geometry, singularity theory with Singular
================================================================================================================

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

This pip-installable distribution ``passagemath-singular``
provides interfaces to `Singular <https://www.singular.uni-kl.de/>`__,
the computer algebra system for polynomial computations, with
special emphasis on commutative and non-commutative algebra, algebraic
geometry, and singularity theory.

It also ships various modules of the Sage library that depend on Singular.


What is included
----------------

- `Cython interface to libSingular <https://passagemath.org/docs/latest/html/en/reference/libs/index.html#libsingular>`_

- `pexpect interface to Singular <https://passagemath.org/docs/latest/html/en/reference/interfaces/sage/interfaces/singular.html>`_

- various other modules, see https://github.com/passagemath/passagemath/blob/main/pkgs/sagemath-singular/MANIFEST.in

- the `PySingular <https://pypi.org/project/PySingular/>`__ API

- The binary wheels published on PyPI include a prebuilt copy of Singular.


Examples
--------

Using Singular on the command line::

    $ pipx run --pip-args="--prefer-binary" --spec "passagemath-singular" sage -singular
                         SINGULAR                                 /
     A Computer Algebra System for Polynomial Computations       /   version 4.4.0
                                                               0<
     by: W. Decker, G.-M. Greuel, G. Pfister, H. Schoenemann     \   Apr 2024
    FB Mathematik der Universitaet, D-67653 Kaiserslautern        \
    >

Finding the installation location of the Singular executable::

    $ pipx run --pip-args="--prefer-binary" --spec "passagemath-singular[test]" ipython

    In [1]: from sage.features.singular import Singular

    In [2]: Singular().absolute_filename()
    Out[2]: '/Users/mkoeppe/.local/pipx/.cache/51651a517394201/lib/python3.11/site-packages/sage_wheels/bin/Singular'

Using the Cython interface to Singular::

    $ pipx run --pip-args="--prefer-binary" --spec "passagemath-singular[test]" ipython

    In [1]: from sage.all__sagemath_singular import *

    In [2]: from sage.libs.singular.function import singular_function

    In [3]: P = PolynomialRing(GF(Integer(7)), names=['a', 'b', 'c', 'd'])

    In [4]: I = sage.rings.ideal.Cyclic(P)

    In [5]: std = singular_function('std')

    In [6]: std(I)
    Out[6]: [a + b + c + d, b^2 + 2*b*d + d^2, b*c^2 + c^2*d - b*d^2 - d^3,
             b*c*d^2 + c^2*d^2 - b*d^3 + c*d^3 - d^4 - 1, b*d^4 + d^5 - b - d,
             c^3*d^2 + c^2*d^3 - c - d, c^2*d^4 + b*c - b*d + c*d - 2*d^2]


Available as extras, from other distributions
---------------------------------------------

Jupyter kernel
~~~~~~~~~~~~~~

``pip install "passagemath-singular[jupyterkernel]"``
 installs the kernel for use in the Jupyter notebook and JupyterLab

``pip install "passagemath-singular[notebook]"``
 installs the kernel and the Jupyter notebook

``pip install "passagemath-singular[jupyterlab]"``
 installs the kernel and JupyterLab
