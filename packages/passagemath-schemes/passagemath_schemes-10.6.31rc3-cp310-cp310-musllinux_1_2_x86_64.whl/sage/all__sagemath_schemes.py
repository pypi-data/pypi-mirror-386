# sage_setup: distribution = sagemath-schemes
# delvewheel: patch
r"""
Top level of the distribution package sagemath-schemes

This distribution makes the following features available::

    sage: from sage.features.sagemath import *
    sage: sage__schemes().is_present()
    FeatureTestResult('sage.schemes', True)
    sage: sage__modular().is_present()
    FeatureTestResult('sage.modular', True)
"""

from .all__sagemath_singular import *

from .all__sagemath_polyhedra import *

from sage.lfunctions.all import *
from sage.modular.all import *
from sage.schemes.all import *
from sage.databases.all__sagemath_schemes import *
from sage.dynamics.all__sagemath_schemes import *
