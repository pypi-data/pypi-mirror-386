# sage_setup: distribution = sagemath-modules
from sage.misc.lazy_import import lazy_import

lazy_import('sage.algebras.group_algebra', 'GroupAlgebra')

lazy_import('sage.algebras.commutative_dga', 'GradedCommutativeAlgebra')

# old-style class for associative algebras, use Parent instead
from sage.rings.ring import Algebra

from sage.algebras.steenrod.all import *
from sage.algebras.finite_dimensional_algebras.all import FiniteDimensionalAlgebra
from sage.algebras.clifford_algebra import CliffordAlgebra, ExteriorAlgebra
from sage.algebras.weyl_algebra import DifferentialWeylAlgebra
lazy_import('sage.algebras.octonion_algebra', 'OctonionAlgebra')

from sage.algebras.lie_algebras.all import *

import sage.algebras.catalog as algebras
del lazy_import
