from collections.abc import Sequence
import enum
from typing import Annotated, overload

import numpy
from numpy.typing import NDArray

from . import opt as opt


class Element:
    @overload
    def __init__(self, arg: str, /) -> None: ...

    @overload
    def __init__(self, arg: int, /) -> None: ...

    @property
    def symbol(self) -> str:
        """The symbol of the element e.g. H, He ..."""

    @property
    def mass(self) -> float:
        """Mass number of the element e.g. 12.01 for C"""

    @property
    def name(self) -> str:
        """The name of the element e.g hydrogen, helium..."""

    @property
    def van_der_waals_radius(self) -> float:
        """Bondi van der Waals radius for element"""

    @property
    def covalent_radius(self) -> float:
        """Covalent radius for element"""

    @property
    def atomic_number(self) -> int:
        """Atomic number e.g. 1, 2 ..."""

    def __gt__(self, arg: Element, /) -> bool: ...

    def __lt__(self, arg: Element, /) -> bool: ...

    def __eq__(self, arg: Element, /) -> bool: ...

    def __ne__(self, arg: Element, /) -> bool: ...

    def __repr__(self) -> str: ...

class Atom:
    def __init__(self, arg0: int, arg1: float, arg2: float, arg3: float, /) -> None: ...

    @property
    def atomic_number(self) -> int:
        """Atomic number for corresponding element"""

    @atomic_number.setter
    def atomic_number(self, arg: int, /) -> None: ...

    @property
    def position(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]:
        """Cartesian position of the atom (Bohr)"""

    @position.setter
    def position(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], /) -> None: ...

    def __repr__(self) -> str: ...

class PointCharge:
    @overload
    def __init__(self, arg0: float, arg1: float, arg2: float, arg3: float, /) -> None: ...

    @overload
    def __init__(self, arg0: float, arg1: Sequence[float], /) -> None: ...

    @overload
    def __init__(self, arg0: float, arg1: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], /) -> None: ...

    @property
    def charge(self) -> float: ...

    @charge.setter
    def charge(self, arg: float, /) -> None: ...

    @property
    def position(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]: ...

    @position.setter
    def position(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], /) -> None: ...

    def __repr__(self) -> str: ...

class Origin(enum.Enum):
    CARTESIAN = 0

    CENTROID = 1

    CENTEROFMASS = 2

class Molecule:
    def __init__(self, arg0: Annotated[NDArray[numpy.int32], dict(shape=(None,), order='C')], arg1: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], /) -> None: ...

    def __len__(self) -> int: ...

    def elements(self) -> list[Element]: ...

    @property
    def positions(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')]: ...

    @property
    def name(self) -> str: ...

    @name.setter
    def name(self, arg: str, /) -> None: ...

    @property
    def partial_charges(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]: ...

    @partial_charges.setter
    def partial_charges(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')], /) -> None: ...

    def esp_partial_charges(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], /) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]: ...

    def atomic_masses(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]: ...

    def atomic_numbers(self) -> Annotated[NDArray[numpy.int32], dict(shape=(None,), order='C')]: ...

    def vdw_radii(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]: ...

    def molar_mass(self) -> float: ...

    def atoms(self) -> list[Atom]: ...

    def bonds(self) -> list[tuple[int, int]]: ...

    def center_of_mass(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]: ...

    def centroid(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]: ...

    def unit_cell_molecule_idx(self) -> int: ...

    def asymmetric_unit_idx(self) -> Annotated[NDArray[numpy.int32], dict(shape=(None,), order='C')]: ...

    def is_equivalent_to(self, arg: Molecule, /) -> bool: ...

    def cell_shift(self) -> Annotated[NDArray[numpy.int32], dict(shape=(3), order='C')]: ...

    @overload
    def rotate(self, rotation: "Eigen::Transform<double, 3, 2, 0>", origin: Origin = Origin.CARTESIAN) -> None:
        """Rotate molecule in-place about origin"""

    @overload
    def rotate(self, rotation: Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')], origin: Origin = Origin.CARTESIAN) -> None:
        """Rotate molecule in-place about origin"""

    @overload
    def rotate(self, rotation: Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')], point: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]) -> None:
        """Rotate molecule in-place about point"""

    @overload
    def transform(self, transform: Annotated[NDArray[numpy.float64], dict(shape=(4, 4), order='F')], origin: Origin = Origin.CARTESIAN) -> None:
        """Transform molecule in-place about origin"""

    @overload
    def transform(self, transform: Annotated[NDArray[numpy.float64], dict(shape=(4, 4), order='F')], point: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]) -> None:
        """Transform molecule in-place about point"""

    def translate(self, translation: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]) -> None:
        """Translate molecule in-place"""

    @overload
    def rotated(self, rotation: "Eigen::Transform<double, 3, 2, 0>", origin: Origin = Origin.CARTESIAN) -> Molecule:
        """Return rotated copy about origin"""

    @overload
    def rotated(self, rotation: Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')], origin: Origin = Origin.CARTESIAN) -> Molecule:
        """Return rotated copy about origin"""

    @overload
    def rotated(self, rotation: Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')], point: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]) -> Molecule:
        """Return rotated copy about point"""

    @overload
    def transformed(self, transform: Annotated[NDArray[numpy.float64], dict(shape=(4, 4), order='F')], origin: Origin = Origin.CARTESIAN) -> Molecule:
        """Return transformed copy about origin"""

    @overload
    def transformed(self, transform: Annotated[NDArray[numpy.float64], dict(shape=(4, 4), order='F')], point: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]) -> Molecule:
        """Return transformed copy about point"""

    def translated(self, translation: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]) -> Molecule:
        """Return translated copy"""

    def centered(self, origin: Origin = Origin.CENTROID) -> Molecule:
        """Return copy centered at origin"""

    @staticmethod
    def from_xyz_file(arg: str, /) -> Molecule: ...

    @staticmethod
    def from_xyz_string(arg: str, /) -> Molecule: ...

    def translational_free_energy(self, arg: float, /) -> float: ...

    def rotational_free_energy(self, arg: float, /) -> float: ...

    def __repr__(self) -> str: ...

class Dimer:
    @overload
    def __init__(self, arg0: Molecule, arg1: Molecule, /) -> None: ...

    @overload
    def __init__(self, arg0: Sequence[Atom], arg1: Sequence[Atom], /) -> None: ...

    @property
    def a(self) -> Molecule: ...

    @property
    def b(self) -> Molecule: ...

    @property
    def nearest_distance(self) -> float: ...

    @property
    def center_of_mass_distance(self) -> float: ...

    @property
    def centroid_distance(self) -> float: ...

    def symmetry_relation(self) -> Annotated[NDArray[numpy.float64], dict(shape=(4, 4), order='F')] | None: ...

    @property
    def name(self) -> str: ...

    @name.setter
    def name(self, arg: str, /) -> None: ...

    def v_ab_com(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]: ...

class AveragingScheme(enum.Enum):
    VOIGT = 0

    REUSS = 1

    HILL = 2

    NUMERICAL = 3

class ElasticTensor:
    def __init__(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(6, 6), writable=False)], /) -> None: ...

    @property
    def tensor(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3, 3, 3, 3), order='C')]: ...

    def youngs_modulus(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], /) -> float: ...

    def linear_compressibility(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], /) -> float: ...

    def shear_modulus(self, arg0: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], arg1: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], /) -> float: ...

    def poisson_ratio(self, arg0: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], arg1: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], /) -> float: ...

    def youngs_modulus_vec(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None, None))], /) -> list[float]:
        """Compute Young's modulus for multiple directions"""

    def shear_modulus_minmax(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3), writable=False)], /) -> tuple[float, float]: ...

    def poisson_ratio_minmax(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3), writable=False)], /) -> tuple[float, float]: ...

    def average_bulk_modulus(self, avg: AveragingScheme = AveragingScheme.HILL) -> float: ...

    def average_shear_modulus(self, avg: AveragingScheme = AveragingScheme.HILL) -> float: ...

    def average_youngs_modulus(self, avg: AveragingScheme = AveragingScheme.HILL) -> float: ...

    def average_poisson_ratio(self, avg: AveragingScheme = AveragingScheme.HILL) -> float: ...

    def average_poisson_ratio_direction(self, direction: Annotated[NDArray[numpy.float64], dict(shape=(3), writable=False)], num_samples: int = 360) -> float:
        """Compute average Poisson's ratio for a given direction"""

    def reduced_youngs_modulus(self, direction: Annotated[NDArray[numpy.float64], dict(shape=(3), writable=False)], num_samples: int = 360) -> float:
        """Compute reduced Young's modulus for a given direction"""

    def transverse_acoustic_velocity(self, bulk_modulus_gpa: float, shear_modulus_gpa: float, density_g_cm3: float) -> float:
        """Compute transverse acoustic velocity V_s = sqrt(G/ρ)"""

    def longitudinal_acoustic_velocity(self, bulk_modulus_gpa: float, shear_modulus_gpa: float, density_g_cm3: float) -> float:
        """Compute longitudinal acoustic velocity V_p = sqrt((4G + 3K)/(3ρ))"""

    @property
    def voigt_s(self) -> Annotated[NDArray[numpy.float64], dict(shape=(6, 6), order='F')]: ...

    @property
    def voigt_c(self) -> Annotated[NDArray[numpy.float64], dict(shape=(6, 6), order='F')]: ...

    def component(self, arg0: int, arg1: int, arg2: int, arg3: int, /) -> float: ...

    def eigenvalues(self) -> Annotated[NDArray[numpy.float64], dict(shape=(6), order='C')]: ...

    def voigt_rotation_matrix(self, rotation: Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')]) -> Annotated[NDArray[numpy.float64], dict(shape=(6, 6), order='F')]:
        """Get the 6x6 Voigt rotation matrix from a 3x3 rotation matrix"""

    def rotate_voigt_stiffness(self, rotation: Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')]) -> Annotated[NDArray[numpy.float64], dict(shape=(6, 6), order='F')]:
        """Rotate the elastic stiffness tensor using a 3x3 rotation matrix"""

    def rotate_voigt_compliance(self, rotation: Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')]) -> Annotated[NDArray[numpy.float64], dict(shape=(6, 6), order='F')]:
        """Rotate the elastic compliance tensor using a 3x3 rotation matrix"""

    def compute_directional_properties(self, n_theta: int = 50, n_phi: int = 50) -> "std::__1::tuple<std::__1::vector<double, std::__1::allocator<double>>, std::__1::vector<double, std::__1::allocator<double>>, std::__1::vector<std::__1::vector<double, std::__1::allocator<double>>, std::__1::allocator<std::__1::vector<double, std::__1::allocator<double>>>>, std::__1::vector<std::__1::vector<double, std::__1::allocator<double>>, std::__1::allocator<std::__1::vector<double, std::__1::allocator<double>>>>>": ...

    def youngs_modulus_with_crystal(self, direction: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], crystal: Crystal) -> float:
        """
        Compute Young's modulus in a given direction (crystal parameter for consistency)
        """

    def reduced_youngs_modulus_with_crystal(self, direction: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], crystal: Crystal, num_samples: int = 360) -> float:
        """Compute reduced Young's modulus in a given direction"""

    def acoustic_velocities_with_crystal(self, crystal: Crystal, scheme: AveragingScheme = AveragingScheme.HILL) -> tuple:
        """
        Compute acoustic velocities using crystal density. Returns (V_s, V_p, density)
        """

class PointGroup(enum.Enum):
    C1 = 0

    Ci = 1

    Cs = 2

    C2 = 3

    C3 = 4

    C4 = 5

    C5 = 6

    C6 = 7

    C8 = 8

    Coov = 9

    Dooh = 10

    C2v = 11

    C3v = 12

    C4v = 13

    C5v = 14

    C6v = 15

    C2h = 16

    C3h = 17

    C4h = 18

    C5h = 19

    C6h = 20

    D2 = 21

    D3 = 22

    D4 = 23

    D5 = 24

    D6 = 25

    D7 = 26

    D8 = 27

    D2h = 28

    D3h = 29

    D4h = 30

    D5h = 31

    D6h = 32

    D7h = 33

    D8h = 34

    D2d = 35

    D3d = 36

    D4d = 37

    D5d = 38

    D6d = 39

    D7d = 40

    D8d = 41

    S4 = 42

    S6 = 43

    S8 = 44

    T = 45

    Td = 46

    Th = 47

    O = 48

    Oh = 49

    I = 50

    Ih = 51

class MirrorType(enum.Enum):
    None = 0

    H = 1

    D = 2

    V = 3

class SymOp:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg0: Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')], arg1: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], /) -> None: ...

    @overload
    def __init__(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(4, 4), order='F')], /) -> None: ...

    def apply(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3, None), writable=False)], /) -> Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')]: ...

    @property
    def rotation(self) -> "Eigen::Block<Eigen::Matrix<double, 4, 4, 0, 4, 4> const, 3, 3, false>": ...

    @property
    def translation(self) -> "Eigen::Block<Eigen::Matrix<double, 4, 4, 0, 4, 4> const, 3, 1, false>": ...

    @property
    def transformation(self) -> Annotated[NDArray[numpy.float64], dict(shape=(4, 4), order='F')]: ...

    @transformation.setter
    def transformation(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(4, 4), order='F')], /) -> None: ...

    @staticmethod
    def from_rotation_vector(arg0: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], arg1: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], /) -> SymOp: ...

    @staticmethod
    def from_axis_angle(arg0: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], arg1: float, arg2: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], /) -> SymOp: ...

    @staticmethod
    def reflection(arg0: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], arg1: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], /) -> SymOp: ...

    @staticmethod
    def rotoreflection(arg0: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], arg1: float, arg2: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], /) -> SymOp: ...

    @staticmethod
    def inversion() -> SymOp: ...

    @staticmethod
    def identity() -> SymOp: ...

class MolecularPointGroup:
    def __init__(self, arg: Molecule, /) -> None: ...

    @property
    def description(self) -> str: ...

    @property
    def point_group_string(self) -> str: ...

    @property
    def point_group(self) -> PointGroup: ...

    @property
    def symops(self) -> list[SymOp]: ...

    @property
    def rotational_symmetries(self) -> list[tuple[Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], int]]: ...

    @property
    def symmetry_number(self) -> int: ...

    def __repr__(self) -> str: ...

def dihedral_group(order: int, mirror_type: MirrorType) -> PointGroup: ...

def cyclic_group(order: int, mirror_type: MirrorType) -> PointGroup: ...

class Monopole:
    def __init__(self) -> None: ...

    @property
    def num_components(self) -> int: ...

    @property
    def charge(self) -> float: ...

    @property
    def components(self) -> list[float]: ...

    @components.setter
    def components(self, arg: Sequence[float], /) -> None: ...

    def to_string(self) -> str: ...

    @overload
    def __add__(self, arg: Monopole, /) -> Monopole: ...

    @overload
    def __add__(self, arg: Dipole, /) -> Dipole: ...

    @overload
    def __add__(self, arg: Quadrupole, /) -> Quadrupole: ...

    @overload
    def __add__(self, arg: Octupole, /) -> Octupole: ...

    @overload
    def __add__(self, arg: Hexadecapole, /) -> Hexadecapole: ...

    def __repr__(self) -> str: ...

class Dipole:
    def __init__(self) -> None: ...

    @property
    def num_components(self) -> int: ...

    @property
    def charge(self) -> float: ...

    @property
    def dipole(self) -> list[float]: ...

    @property
    def components(self) -> list[float]: ...

    @components.setter
    def components(self, arg: Sequence[float], /) -> None: ...

    def to_string(self) -> str: ...

    @overload
    def __add__(self, arg: Monopole, /) -> Dipole: ...

    @overload
    def __add__(self, arg: Dipole, /) -> Dipole: ...

    @overload
    def __add__(self, arg: Quadrupole, /) -> Quadrupole: ...

    @overload
    def __add__(self, arg: Octupole, /) -> Octupole: ...

    @overload
    def __add__(self, arg: Hexadecapole, /) -> Hexadecapole: ...

    def __repr__(self) -> str: ...

class Quadrupole:
    def __init__(self) -> None: ...

    @property
    def num_components(self) -> int: ...

    @property
    def charge(self) -> float: ...

    @property
    def dipole(self) -> list[float]: ...

    @property
    def quadrupole(self) -> list[float]: ...

    @property
    def components(self) -> list[float]: ...

    @components.setter
    def components(self, arg: Sequence[float], /) -> None: ...

    def to_string(self) -> str: ...

    @overload
    def __add__(self, arg: Monopole, /) -> Quadrupole: ...

    @overload
    def __add__(self, arg: Dipole, /) -> Quadrupole: ...

    @overload
    def __add__(self, arg: Quadrupole, /) -> Quadrupole: ...

    @overload
    def __add__(self, arg: Octupole, /) -> Octupole: ...

    @overload
    def __add__(self, arg: Hexadecapole, /) -> Hexadecapole: ...

    def __repr__(self) -> str: ...

class Octupole:
    def __init__(self) -> None: ...

    @property
    def num_components(self) -> int: ...

    @property
    def charge(self) -> float: ...

    @property
    def dipole(self) -> list[float]: ...

    @property
    def quadrupole(self) -> list[float]: ...

    @property
    def octupole(self) -> list[float]: ...

    @property
    def components(self) -> list[float]: ...

    @components.setter
    def components(self, arg: Sequence[float], /) -> None: ...

    def to_string(self) -> str: ...

    @overload
    def __add__(self, arg: Monopole, /) -> Octupole: ...

    @overload
    def __add__(self, arg: Dipole, /) -> Octupole: ...

    @overload
    def __add__(self, arg: Quadrupole, /) -> Octupole: ...

    @overload
    def __add__(self, arg: Octupole, /) -> Octupole: ...

    @overload
    def __add__(self, arg: Hexadecapole, /) -> Hexadecapole: ...

    def __repr__(self) -> str: ...

class Hexadecapole:
    def __init__(self) -> None: ...

    @property
    def num_components(self) -> int: ...

    @property
    def charge(self) -> float: ...

    @property
    def dipole(self) -> list[float]: ...

    @property
    def quadrupole(self) -> list[float]: ...

    @property
    def octupole(self) -> list[float]: ...

    @property
    def hexadecapole(self) -> list[float]: ...

    @property
    def components(self) -> list[float]: ...

    @components.setter
    def components(self, arg: Sequence[float], /) -> None: ...

    def to_string(self) -> str: ...

    @overload
    def __add__(self, arg: Monopole, /) -> Hexadecapole: ...

    @overload
    def __add__(self, arg: Dipole, /) -> Hexadecapole: ...

    @overload
    def __add__(self, arg: Quadrupole, /) -> Hexadecapole: ...

    @overload
    def __add__(self, arg: Octupole, /) -> Hexadecapole: ...

    @overload
    def __add__(self, arg: Hexadecapole, /) -> Hexadecapole: ...

    def __repr__(self) -> str: ...

@overload
def Multipole(order: int) -> object:
    """Create a multipole of specified order"""

@overload
def Multipole(order: int, components: Sequence[float]) -> object:
    """Create a multipole of specified order with components"""

class MatTriple:
    def __init__(self) -> None: ...

    @property
    def x(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    @x.setter
    def x(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], /) -> None: ...

    @property
    def y(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    @y.setter
    def y(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], /) -> None: ...

    @property
    def z(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    @z.setter
    def z(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], /) -> None: ...

    def scale_by(self, arg: float, /) -> None: ...

    def symmetrize(self) -> None: ...

    def __add__(self, arg: MatTriple, /) -> MatTriple: ...

    def __sub__(self, arg: MatTriple, /) -> MatTriple: ...

    def __repr__(self) -> str: ...

def eem_partial_charges(atomic_numbers: Annotated[NDArray[numpy.int32], dict(shape=(None,), order='C')], positions: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], _charge: float = 0.0) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]: ...

def eeq_partial_charges(atomic_numbers: Annotated[NDArray[numpy.int32], dict(shape=(None,), order='C')], positions: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], _charge: float = 0.0) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]: ...

def eeq_coordination_numbers(atomic_numbers: Annotated[NDArray[numpy.int32], dict(shape=(None,), order='C')], positions: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')]) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]: ...

def quasirandom_kgf(ndims: int, count: int, seed: int = 0) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

class LogLevel(enum.Enum):
    TRACE = 0

    DEBUG = 1

    INFO = 2

    WARN = 3

    ERROR = 4

    CRITICAL = 5

    OFF = 6

@overload
def set_log_level(level: LogLevel) -> None:
    """Set the log level"""

@overload
def set_log_level(level: str) -> None:
    """Set the log level from string"""

@overload
def set_log_level(level: int) -> None:
    """Set the log level from int"""

@overload
def set_log_level(arg: int, /) -> None: ...

@overload
def set_log_level(arg: LogLevel, /) -> None: ...

@overload
def set_log_level(arg: str, /) -> None: ...

def register_log_callback(callback: object) -> None:
    """Register a callback function to receive log messages"""

def clear_log_callbacks() -> None:
    """Clear all registered log callbacks"""

def get_buffered_logs() -> list:
    """Get all buffered log messages"""

def clear_log_buffer() -> None:
    """Clear the log buffer"""

def set_log_buffering(enable: bool) -> None:
    """Enable or disable log buffering"""

def log_trace(message: str) -> None:
    """Log a trace message"""

def log_debug(message: str) -> None:
    """Log a debug message"""

def log_info(message: str) -> None:
    """Log an info message"""

def log_warn(message: str) -> None:
    """Log a warning message"""

def log_error(message: str) -> None:
    """Log an error message"""

def log_critical(message: str) -> None:
    """Log a critical message"""

class LatticeConvergenceSettings:
    def __init__(self) -> None: ...

    @property
    def min_radius(self) -> float: ...

    @min_radius.setter
    def min_radius(self, arg: float, /) -> None: ...

    @property
    def max_radius(self) -> float: ...

    @max_radius.setter
    def max_radius(self, arg: float, /) -> None: ...

    @property
    def radius_increment(self) -> float: ...

    @radius_increment.setter
    def radius_increment(self, arg: float, /) -> None: ...

    @property
    def energy_tolerance(self) -> float: ...

    @energy_tolerance.setter
    def energy_tolerance(self, arg: float, /) -> None: ...

    @property
    def wolf_sum(self) -> bool: ...

    @wolf_sum.setter
    def wolf_sum(self, arg: bool, /) -> None: ...

    @property
    def crystal_field_polarization(self) -> bool: ...

    @crystal_field_polarization.setter
    def crystal_field_polarization(self, arg: bool, /) -> None: ...

    @property
    def model_name(self) -> str: ...

    @model_name.setter
    def model_name(self, arg: str, /) -> None: ...

    @property
    def crystal_filename(self) -> str: ...

    @crystal_filename.setter
    def crystal_filename(self, arg: str, /) -> None: ...

    @property
    def output_json_filename(self) -> str: ...

    @output_json_filename.setter
    def output_json_filename(self, arg: str, /) -> None: ...

class CrystalGrowthConfig:
    def __init__(self) -> None: ...

    @property
    def lattice_settings(self) -> LatticeConvergenceSettings: ...

    @lattice_settings.setter
    def lattice_settings(self, arg: LatticeConvergenceSettings, /) -> None: ...

    @property
    def cg_radius(self) -> float: ...

    @cg_radius.setter
    def cg_radius(self, arg: float, /) -> None: ...

    @property
    def solvent(self) -> str: ...

    @solvent.setter
    def solvent(self, arg: str, /) -> None: ...

    @property
    def wavefunction_choice(self) -> str: ...

    @wavefunction_choice.setter
    def wavefunction_choice(self, arg: str, /) -> None: ...

    @property
    def num_surface_energies(self) -> int: ...

    @num_surface_energies.setter
    def num_surface_energies(self, arg: int, /) -> None: ...

class DimerSolventTerm:
    @property
    def ab(self) -> float: ...

    @property
    def ba(self) -> float: ...

    @property
    def total(self) -> float: ...

class DimerResult:
    def __init__(self, arg0: Dimer, arg1: bool, arg2: int, /) -> None: ...

    @property
    def dimer(self) -> Dimer: ...

    @property
    def unique_idx(self) -> int: ...

    def set_energy_component(self, arg0: str, arg1: float, /) -> None: ...

    def total_energy(self) -> float: ...

    def energy_component(self, arg: str, /) -> float: ...

    def energy_components(self) -> dict: ...

    @property
    def is_nearest_neighbor(self) -> bool: ...

class MoleculeResult:
    @property
    def dimer_results(self) -> list[DimerResult]: ...

    @property
    def total(self) -> CrystalGrowthEnergyTotal: ...

    @property
    def has_inversion_symmetry(self) -> bool: ...

    def total_energy(self) -> float: ...

    def energy_components(self) -> dict: ...

    def energy_component(self, arg: str, /) -> float: ...

class CrystalGrowthResult:
    @property
    def molecule_results(self) -> list[MoleculeResult]: ...

class CrystalGrowthEnergyTotal:
    @property
    def crystal(self) -> float: ...

    @property
    def int(self) -> float: ...

    @property
    def solution(self) -> float: ...

    def __repr__(self) -> str: ...

class InteractionMapper:
    def __init__(self, arg0: Crystal, arg1: CrystalDimers, arg2: CrystalDimers, arg3: bool, /) -> None: ...

    def map_interactions(self, arg0: Sequence[float], arg1: Sequence[Sequence[DimerResult]], /) -> list[float]: ...

class HKL:
    def __init__(self, arg0: int, arg1: int, arg2: int, /) -> None: ...

    def d(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')], /) -> float: ...

    @staticmethod
    def floor(arg0: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], arg1: float, /) -> HKL: ...

    @staticmethod
    def ceil(arg: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], /) -> HKL: ...

    @staticmethod
    def maximum() -> HKL: ...

    @staticmethod
    def minimum() -> HKL: ...

    def vector(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]: ...

    @property
    def h(self) -> int: ...

    @h.setter
    def h(self, arg: int, /) -> None: ...

    @property
    def k(self) -> int: ...

    @k.setter
    def k(self, arg: int, /) -> None: ...

    @property
    def l(self) -> int: ...

    @l.setter
    def l(self, arg: int, /) -> None: ...

    def __repr__(self) -> str: ...

class SymmetryOperationFormat:
    def __init__(self) -> None: ...

    @property
    def fmt_string(self) -> str: ...

    @fmt_string.setter
    def fmt_string(self, arg: str, /) -> None: ...

    @property
    def delimiter(self) -> str: ...

    @delimiter.setter
    def delimiter(self, arg: str, /) -> None: ...

class SymmetryOperation:
    @overload
    def __init__(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(4, 4), order='F')], /) -> None:
        """Construct from 4x4 Seitz matrix"""

    @overload
    def __init__(self, arg: str, /) -> None:
        """Construct from string representation (e.g. 'x,y,z')"""

    @overload
    def __init__(self, arg: int, /) -> None:
        """Construct from integer representation"""

    def to_int(self) -> int:
        """Get integer representation of the symmetry operation"""

    def to_string(self, format: SymmetryOperationFormat = ...) -> str:
        """Get string representation of the symmetry operation"""

    def inverted(self) -> SymmetryOperation:
        """Get inverted copy of the symmetry operation"""

    def translated(self, arg0: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], arg1: bool, /) -> SymmetryOperation:
        """Get translated copy of the symmetry operation"""

    def is_identity(self) -> bool:
        """Check if this is the identity operation"""

    def apply(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], /) -> Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')]:
        """Apply transformation to coordinates"""

    def seitz(self) -> Annotated[NDArray[numpy.float64], dict(shape=(4, 4), order='F')]:
        """Get the 4x4 Seitz matrix"""

    def rotation(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')]:
        """Get the 3x3 rotation matrix"""

    def cartesian_rotation(self, arg: UnitCell, /) -> Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')]:
        """Get rotation matrix in Cartesian coordinates"""

    def rotate_adp(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(6), writable=False)], /) -> Annotated[NDArray[numpy.float64], dict(shape=(6), order='C')]:
        """Rotate anisotropic displacement parameters"""

    def translation(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]:
        """Get translation vector"""

    def has_translation(self) -> bool:
        """Check if operation includes translation"""

    def __call__(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], /) -> Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')]: ...

    def __eq__(self, arg: SymmetryOperation, /) -> bool: ...

    def __lt__(self, arg: SymmetryOperation, /) -> bool: ...

    def __gt__(self, arg: SymmetryOperation, /) -> bool: ...

    def __le__(self, arg: SymmetryOperation, /) -> bool: ...

    def __ge__(self, arg: SymmetryOperation, /) -> bool: ...

    def __mul__(self, arg: SymmetryOperation, /) -> SymmetryOperation:
        """Compose two symmetry operations"""

    def __repr__(self) -> str: ...

class SpaceGroup:
    @overload
    def __init__(self) -> None:
        """Constructs a space group with only translational symmetry"""

    @overload
    def __init__(self, arg: int, /) -> None:
        """Constructs a space group with the given space group number"""

    @overload
    def __init__(self, arg: str, /) -> None:
        """Constructs a space group with the given space group symbol"""

    @overload
    def __init__(self, arg: Sequence[str], /) -> None:
        """
        Constructs a space group with the list of symmetry operations in string form
        """

    @overload
    def __init__(self, arg: Sequence[SymmetryOperation], /) -> None:
        """Constructs a space group with the list of symmetry operations"""

    def number(self) -> int:
        """Returns the space group number"""

    @property
    def symbol(self) -> str:
        """Returns the Hermann-Mauguin (international tables) symbol"""

    @property
    def short_name(self) -> str:
        """Returns the shortened Hermann-Mauguin symbol"""

    @property
    def symmetry_operations(self) -> list[SymmetryOperation]:
        """Returns the list of symmetry operations"""

    def has_H_R_choice(self) -> bool:
        """Determines whether this space group has hexagonal/rhombohedral choice"""

    def apply_all_symmetry_operations(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], /) -> tuple[Annotated[NDArray[numpy.int32], dict(shape=(None,), order='C')], Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')]]:
        """Apply all symmetry operations to fractional coordinates"""

    def apply_rotations(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], /) -> tuple[Annotated[NDArray[numpy.int32], dict(shape=(None,), order='C')], Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')]]:
        """Apply rotation parts of symmetry operations to fractional coordinates"""

    def __repr__(self) -> str: ...

class Crystal:
    def __init__(self, arg0: AsymmetricUnit, arg1: SpaceGroup, arg2: UnitCell, /) -> None: ...

    def symmetry_unique_molecules(self) -> list[Molecule]: ...

    def symmetry_unique_dimers(self, arg: float, /) -> CrystalDimers: ...

    def unit_cell(self) -> UnitCell: ...

    def unit_cell_molecules(self) -> list[Molecule]: ...

    def unit_cell_atoms(self) -> CrystalAtomRegion: ...

    def unit_cell_dimers(self, arg: float, /) -> CrystalDimers: ...

    def atom_surroundings(self, arg0: int, arg1: float, /) -> CrystalAtomRegion: ...

    def dimer_symmetry_string(self, arg: Dimer, /) -> str: ...

    @overload
    def normalize_hydrogen_bondlengths(self, custom_lengths: dict = {}) -> int:
        """
        Normalize hydrogen bond lengths to standard values.
        Returns the number of hydrogens normalized.
        custom_lengths: optional dict mapping atomic numbers to bond lengths in Angstroms
        """

    @overload
    def normalize_hydrogen_bondlengths(self) -> int:
        """
        Normalize hydrogen bond lengths to standard values.
        Returns the number of hydrogens normalized.
        """

    def asymmetric_unit_atom_surroundings(self, arg: float, /) -> list[CrystalAtomRegion]: ...

    def num_sites(self) -> int: ...

    def labels(self) -> list[str]: ...

    def to_fractional(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], /) -> Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')]: ...

    def to_cartesian(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], /) -> Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')]: ...

    def volume(self) -> float: ...

    def density(self) -> float:
        """Crystal density in g/cm³"""

    def slab(self, arg0: HKL, arg1: HKL, /) -> CrystalAtomRegion: ...

    def asymmetric_unit(self) -> AsymmetricUnit: ...

    @staticmethod
    def create_primitive_supercell(arg0: Crystal, arg1: HKL, /) -> Crystal: ...

    @staticmethod
    def from_cif_file(arg: str, /) -> Crystal: ...

    @staticmethod
    def from_cif_string(arg: str, /) -> Crystal: ...

    def __repr__(self) -> str: ...

class CrystalAtomRegion:
    @property
    def frac_pos(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')]: ...

    @property
    def cart_pos(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')]: ...

    @property
    def asym_idx(self) -> Annotated[NDArray[numpy.int32], dict(shape=(None,), order='C')]: ...

    @property
    def atomic_numbers(self) -> Annotated[NDArray[numpy.int32], dict(shape=(None,), order='C')]: ...

    @property
    def symop(self) -> Annotated[NDArray[numpy.int32], dict(shape=(None,), order='C')]: ...

    def size(self) -> int: ...

    def __repr__(self) -> str: ...

class SymmetryRelatedDimer:
    @property
    def unique_index(self) -> int: ...

    @property
    def dimer(self) -> Dimer: ...

class CrystalDimers:
    @property
    def radius(self) -> float: ...

    @property
    def unique_dimers(self) -> list[Dimer]: ...

    @property
    def molecule_neighbors(self) -> list[list[SymmetryRelatedDimer]]: ...

class AsymmetricUnit:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg0: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], arg1: Annotated[NDArray[numpy.int32], dict(shape=(None,), order='C')], /) -> None: ...

    @overload
    def __init__(self, arg0: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], arg1: Annotated[NDArray[numpy.int32], dict(shape=(None,), order='C')], arg2: Sequence[str], /) -> None: ...

    @property
    def positions(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')]: ...

    @positions.setter
    def positions(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], /) -> None: ...

    @property
    def atomic_numbers(self) -> Annotated[NDArray[numpy.int32], dict(shape=(None,), order='C')]: ...

    @atomic_numbers.setter
    def atomic_numbers(self, arg: Annotated[NDArray[numpy.int32], dict(shape=(None,), order='C')], /) -> None: ...

    @property
    def occupations(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]: ...

    @occupations.setter
    def occupations(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')], /) -> None: ...

    @property
    def charges(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]: ...

    @charges.setter
    def charges(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')], /) -> None: ...

    @property
    def labels(self) -> list[str]: ...

    @labels.setter
    def labels(self, arg: Sequence[str], /) -> None: ...

    def __len__(self) -> int: ...

    def __repr__(self) -> str: ...

class UnitCell:
    @overload
    def __init__(self) -> None:
        """Default constructor"""

    @overload
    def __init__(self, arg0: float, arg1: float, arg2: float, arg3: float, arg4: float, arg5: float, /) -> None:
        """Construct with lengths (a,b,c) and angles (alpha,beta,gamma)"""

    @overload
    def __init__(self, arg0: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], arg1: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], /) -> None:
        """Construct with lengths and angles vectors"""

    @overload
    def __init__(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')], /) -> None:
        """Construct from lattice vectors matrix"""

    @property
    def a(self) -> float:
        """Length of a-axis in Angstroms"""

    @a.setter
    def a(self, arg: float, /) -> None: ...

    @property
    def b(self) -> float:
        """Length of b-axis in Angstroms"""

    @b.setter
    def b(self, arg: float, /) -> None: ...

    @property
    def c(self) -> float:
        """Length of c-axis in Angstroms"""

    @c.setter
    def c(self, arg: float, /) -> None: ...

    @property
    def alpha(self) -> float:
        """Angle between b and c axes in radians"""

    @alpha.setter
    def alpha(self, arg: float, /) -> None: ...

    @property
    def beta(self) -> float:
        """Angle between a and c axes in radians"""

    @beta.setter
    def beta(self, arg: float, /) -> None: ...

    @property
    def gamma(self) -> float:
        """Angle between a and b axes in radians"""

    @gamma.setter
    def gamma(self, arg: float, /) -> None: ...

    @property
    def volume(self) -> float:
        """Volume of the unit cell in cubic Angstroms"""

    @property
    def direct(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')]:
        """Direct matrix (columns are lattice vectors)"""

    @property
    def reciprocal(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')]:
        """Reciprocal matrix (columns are reciprocal lattice vectors)"""

    @property
    def inverse(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')]:
        """Inverse matrix (rows are reciprocal lattice vectors)"""

    @property
    def lengths(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]:
        """Vector of lengths (a,b,c)"""

    @property
    def angles(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]:
        """Vector of angles (alpha,beta,gamma)"""

    def is_cubic(self) -> bool: ...

    def is_triclinic(self) -> bool: ...

    def is_monoclinic(self) -> bool: ...

    def is_orthorhombic(self) -> bool: ...

    def is_tetragonal(self) -> bool: ...

    def is_rhombohedral(self) -> bool: ...

    def is_hexagonal(self) -> bool: ...

    def is_orthogonal(self) -> bool: ...

    def cell_type(self) -> str:
        """Get string representation of cell type"""

    def to_cartesian(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], /) -> Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')]:
        """Convert fractional to Cartesian coordinates"""

    def to_fractional(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], /) -> Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')]:
        """Convert Cartesian to fractional coordinates"""

    def to_reciprocal(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], /) -> Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')]:
        """Convert coordinates to reciprocal space"""

    def to_cartesian_adp(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(6, None), order='F')], /) -> Annotated[NDArray[numpy.float64], dict(shape=(6, None), order='F')]:
        """Convert ADPs from fractional to Cartesian coordinates"""

    def to_fractional_adp(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(6, None), order='F')], /) -> Annotated[NDArray[numpy.float64], dict(shape=(6, None), order='F')]:
        """Convert ADPs from Cartesian to fractional coordinates"""

    def hkl_limits(self, arg: float, /) -> HKL:
        """Get HKL limits for given minimum d-spacing"""

    def a_vector(self) -> "Eigen::Block<Eigen::Matrix<double, 3, 3, 0, 3, 3> const, 3, 1, true>":
        """Get a lattice vector"""

    def b_vector(self) -> "Eigen::Block<Eigen::Matrix<double, 3, 3, 0, 3, 3> const, 3, 1, true>":
        """Get b lattice vector"""

    def c_vector(self) -> "Eigen::Block<Eigen::Matrix<double, 3, 3, 0, 3, 3> const, 3, 1, true>":
        """Get c lattice vector"""

    def a_star_vector(self) -> "Eigen::Block<Eigen::Matrix<double, 3, 3, 0, 3, 3> const, 3, 1, true>":
        """Get a* reciprocal vector"""

    def b_star_vector(self) -> "Eigen::Block<Eigen::Matrix<double, 3, 3, 0, 3, 3> const, 3, 1, true>":
        """Get b* reciprocal vector"""

    def c_star_vector(self) -> "Eigen::Block<Eigen::Matrix<double, 3, 3, 0, 3, 3> const, 3, 1, true>":
        """Get c* reciprocal vector"""

    def __repr__(self) -> str: ...

def cubic_cell(length: float) -> UnitCell:
    """Create cubic unit cell"""

def rhombohedral_cell(length: float, angle: float) -> UnitCell:
    """Create rhombohedral unit cell"""

def tetragonal_cell(a: float, c: float) -> UnitCell:
    """Create tetragonal unit cell"""

def hexagonal_cell(a: float, c: float) -> UnitCell:
    """Create hexagonal unit cell"""

def orthorhombic_cell(a: float, b: float, c: float) -> UnitCell:
    """Create orthorhombic unit cell"""

def monoclinic_cell(a: float, b: float, c: float, angle: float) -> UnitCell:
    """Create monoclinic unit cell"""

def triclinic_cell(a: float, b: float, c: float, alpha: float, beta: float, gamma: float) -> UnitCell:
    """Create triclinic unit cell"""

class SiteIndex:
    @property
    def offset(self) -> int: ...

    @property
    def hkl(self) -> int: ...

    def __repr__(self) -> str: ...

class DimerIndex:
    def __init__(self, arg0: SiteIndex, arg1: SiteIndex, /) -> None: ...

    @property
    def a(self) -> SiteIndex: ...

    @property
    def b(self) -> SiteIndex: ...

    def hkl_difference(self) -> HKL: ...

    def __eq__(self, arg: DimerIndex, /) -> bool: ...

    def __lt__(self, arg: DimerIndex, /) -> bool: ...

    def __repr__(self) -> str: ...

class DimerMappingTable:
    @staticmethod
    def build_dimer_table(crystal: Crystal, dimers: CrystalDimers, consider_inversion: bool) -> DimerMappingTable: ...

    def symmetry_unique_dimer(self, arg: DimerIndex, /) -> DimerIndex: ...

    def symmetry_related_dimers(self, arg: DimerIndex, /) -> list[DimerIndex]: ...

    @property
    def unique_dimers(self) -> list[DimerIndex]: ...

    @property
    def symmetry_unique_dimers(self) -> list[DimerIndex]: ...

    def dimer_positions(self, arg: Dimer, /) -> tuple[Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]]: ...

    @overload
    def dimer_index(self, arg: Dimer, /) -> DimerIndex: ...

    @overload
    def dimer_index(self, arg0: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], arg1: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], /) -> DimerIndex: ...

    @staticmethod
    def normalized_dimer_index(arg: DimerIndex, /) -> DimerIndex: ...

    def canonical_dimer_index(self, arg: DimerIndex, /) -> DimerIndex: ...

    def __repr__(self) -> str: ...

class SurfaceCutResult:
    def __init__(self, arg: CrystalDimers, /) -> None: ...

    @property
    def molecules(self) -> list[Molecule]: ...

    @molecules.setter
    def molecules(self, arg: Sequence[Molecule], /) -> None: ...

    @property
    def exyz(self) -> str: ...

    @exyz.setter
    def exyz(self, arg: str, /) -> None: ...

    @property
    def above(self) -> list[list[int]]: ...

    @above.setter
    def above(self, arg: Sequence[Sequence[int]], /) -> None: ...

    @property
    def below(self) -> list[list[int]]: ...

    @below.setter
    def below(self, arg: Sequence[Sequence[int]], /) -> None: ...

    @property
    def slab(self) -> list[list[int]]: ...

    @slab.setter
    def slab(self, arg: Sequence[Sequence[int]], /) -> None: ...

    @property
    def bulk(self) -> list[list[int]]: ...

    @bulk.setter
    def bulk(self, arg: Sequence[Sequence[int]], /) -> None: ...

    @property
    def depth_scale(self) -> float: ...

    @depth_scale.setter
    def depth_scale(self, arg: float, /) -> None: ...

    @property
    def basis(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')]: ...

    @basis.setter
    def basis(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')], /) -> None: ...

    @property
    def cut_offset(self) -> float: ...

    @cut_offset.setter
    def cut_offset(self, arg: float, /) -> None: ...

    def total_above(self, arg: CrystalDimers, /) -> float: ...

    def total_below(self, arg: CrystalDimers, /) -> float: ...

    def total_slab(self, arg: CrystalDimers, /) -> float: ...

    def total_bulk(self, arg: CrystalDimers, /) -> float: ...

    def unique_counts_above(self, arg: CrystalDimers, /) -> list[list[int]]: ...

    def __repr__(self) -> str: ...

class CrystalSurfaceGenerationParameters:
    def __init__(self) -> None: ...

    @property
    def d_min(self) -> float: ...

    @d_min.setter
    def d_min(self, arg: float, /) -> None: ...

    @property
    def d_max(self) -> float: ...

    @d_max.setter
    def d_max(self, arg: float, /) -> None: ...

    @property
    def unique(self) -> bool: ...

    @unique.setter
    def unique(self, arg: bool, /) -> None: ...

    @property
    def reduced(self) -> bool: ...

    @reduced.setter
    def reduced(self, arg: bool, /) -> None: ...

    @property
    def systematic_absences_allowed(self) -> bool: ...

    @systematic_absences_allowed.setter
    def systematic_absences_allowed(self, arg: bool, /) -> None: ...

class Surface:
    def __init__(self, arg0: HKL, arg1: Crystal, /) -> None: ...

    def depth(self) -> float: ...

    def d(self) -> float: ...

    def print(self) -> None: ...

    def normal_vector(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]: ...

    @property
    def hkl(self) -> HKL: ...

    @property
    def depth_vector(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]: ...

    @property
    def a_vector(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]: ...

    @property
    def b_vector(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]: ...

    def area(self) -> float: ...

    def dipole(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]: ...

    def basis_matrix(self, depth_scale: float = 1.0) -> Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')]: ...

    def find_molecule_cell_translations(self, unit_cell_mols: Sequence[Molecule], depth: float, cut_offset: float = 0.0) -> list[Molecule]: ...

    def count_crystal_dimers_cut_by_surface(self, dimers: CrystalDimers, cut_offset: float = 0.0) -> SurfaceCutResult: ...

    def possible_cuts(self, unique_positions: Annotated[NDArray[numpy.float64], dict(shape=(3, None), writable=False)], epsilon: float = 1e-06) -> list[float]: ...

    @staticmethod
    def check_systematic_absence(arg0: Crystal, arg1: HKL, /) -> bool: ...

    @staticmethod
    def faces_are_equivalent(arg0: Crystal, arg1: HKL, arg2: HKL, /) -> bool: ...

    def __repr__(self) -> str: ...

def generate_surfaces(crystal: Crystal, params: CrystalSurfaceGenerationParameters = ...) -> list[Surface]: ...

class PDDConfig:
    def __init__(self) -> None: ...

    @property
    def lexsort(self) -> bool:
        """Lexicographically sort rows"""

    @lexsort.setter
    def lexsort(self, arg: bool, /) -> None: ...

    @property
    def collapse(self) -> bool:
        """Merge similar rows within tolerance"""

    @collapse.setter
    def collapse(self, arg: bool, /) -> None: ...

    @property
    def collapse_tol(self) -> float:
        """Tolerance for merging rows (Chebyshev distance)"""

    @collapse_tol.setter
    def collapse_tol(self, arg: float, /) -> None: ...

    @property
    def return_groups(self) -> bool:
        """Return grouping information"""

    @return_groups.setter
    def return_groups(self, arg: bool, /) -> None: ...

class PDD:
    @overload
    def __init__(self, crystal: Crystal, k: int) -> None:
        """Construct PDD from crystal structure with k nearest neighbors"""

    @overload
    def __init__(self, crystal: Crystal, k: int, config: PDDConfig) -> None:
        """
        Construct PDD from crystal structure with k nearest neighbors and configuration
        """

    @property
    def weights(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]:
        """Get the weights for each environment"""

    @property
    def distances(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]:
        """Get the distance matrix (environments as columns)"""

    def average_minimum_distance(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]:
        """Calculate Average Minimum Distance from this PDD"""

    def matrix(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]:
        """Get the full PDD matrix (weights + distances)"""

    def size(self) -> int:
        """Number of unique chemical environments"""

    def k(self) -> int:
        """Number of neighbors considered"""

    @property
    def groups(self) -> Annotated[NDArray[numpy.int32], dict(shape=(None, None), order='F')]:
        """Get grouping information if available"""

class Steinhardt:
    def __init__(self, lmax: int) -> None:
        """Initialize Steinhardt descriptor with maximum l value"""

    def compute_q(self, positions: Annotated[NDArray[numpy.float64], dict(shape=(3, None), writable=False)]) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]:
        """Compute Steinhardt Q parameters for given positions"""

    def compute_w(self, positions: Annotated[NDArray[numpy.float64], dict(shape=(3, None), writable=False)]) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]:
        """Compute Steinhardt W parameters for given positions"""

    def compute_qlm(self, positions: Annotated[NDArray[numpy.float64], dict(shape=(3, None), writable=False)]) -> Annotated[NDArray[numpy.complex128], dict(shape=(None,), order='C')]:
        """Compute complex Steinhardt Q_lm parameters for given positions"""

    def compute_averaged_q(self, positions: Annotated[NDArray[numpy.float64], dict(shape=(3, None), writable=False)], radius: float = 6.0) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]:
        """Compute locally averaged Steinhardt Q parameters"""

    def compute_averaged_w(self, positions: Annotated[NDArray[numpy.float64], dict(shape=(3, None), writable=False)], radius: float = 6.0) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]:
        """Compute locally averaged Steinhardt W parameters"""

    def precompute_wigner3j_coefficients(self) -> None:
        """Precompute Wigner 3j coefficients for better performance"""

    def size(self) -> int:
        """Number of l values (lmax + 1)"""

    def nlm(self) -> int:
        """Total number of (l,m) combinations"""

class PromoleculeInterpolatorParameters:
    def __init__(self) -> None: ...

    @property
    def num_points(self) -> int:
        """Number of interpolation points"""

    @num_points.setter
    def num_points(self, arg: int, /) -> None: ...

    @property
    def domain_lower(self) -> float:
        """Lower bound of interpolation domain"""

    @domain_lower.setter
    def domain_lower(self, arg: float, /) -> None: ...

    @property
    def domain_upper(self) -> float:
        """Upper bound of interpolation domain"""

    @domain_upper.setter
    def domain_upper(self, arg: float, /) -> None: ...

class PromoleculeAtomInterpolator:
    def __init__(self) -> None: ...

    @property
    def positions(self) -> Annotated[NDArray[numpy.float32], dict(shape=(3, None), order='F')]:
        """Atomic positions"""

    @positions.setter
    def positions(self, arg: Annotated[NDArray[numpy.float32], dict(shape=(3, None), order='F')], /) -> None: ...

    @property
    def threshold(self) -> float:
        """Distance threshold for interpolation"""

    @threshold.setter
    def threshold(self, arg: float, /) -> None: ...

class SpinorbitalKind(enum.Enum):
    Restricted = 0

    Unrestricted = 1

    General = 2

class Shell:
    def __init__(self, arg0: PointCharge, arg1: float, /) -> None: ...

    @property
    def origin(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]:
        """shell position/origin (Bohr)"""

    @property
    def exponents(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]:
        """array of exponents for primitives in this shell"""

    @property
    def contraction_coefficients(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]:
        """array of contraction coefficients for in this shell"""

    def num_contractions(self) -> int:
        """number of contractions"""

    def num_primitives(self) -> int:
        """number of primitive gaussians"""

    def norm(self) -> float:
        """norm of the shell"""

    def __repr__(self) -> str: ...

class AOBasis:
    @staticmethod
    def load(arg0: Sequence[Atom], arg1: str, /) -> AOBasis: ...

    def shells(self) -> list[Shell]: ...

    def set_pure(self, arg: bool, /) -> None: ...

    def size(self) -> int: ...

    def nbf(self) -> int: ...

    def atoms(self) -> list[Atom]: ...

    def first_bf(self) -> list[int]: ...

    def bf_to_shell(self) -> list[int]: ...

    def bf_to_atom(self) -> list[int]: ...

    def shell_to_atom(self) -> list[int]: ...

    def atom_to_shell(self) -> list[list[int]]: ...

    def l_max(self) -> int: ...

    def name(self) -> str: ...

    def evaluate(self, points: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], derivatives: int = 0) -> GTOValues: ...

    def __repr__(self) -> str: ...

class MolecularOrbitals:
    def __init__(self) -> None: ...

    @property
    def kind(self) -> SpinorbitalKind: ...

    @kind.setter
    def kind(self, arg: SpinorbitalKind, /) -> None: ...

    @property
    def num_alpha(self) -> int: ...

    @num_alpha.setter
    def num_alpha(self, arg: int, /) -> None: ...

    @property
    def num_beta(self) -> int: ...

    @num_beta.setter
    def num_beta(self, arg: int, /) -> None: ...

    @property
    def num_ao(self) -> int: ...

    @num_ao.setter
    def num_ao(self, arg: int, /) -> None: ...

    @property
    def orbital_coeffs(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    @orbital_coeffs.setter
    def orbital_coeffs(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], /) -> None: ...

    @property
    def occupied_orbital_coeffs(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    @occupied_orbital_coeffs.setter
    def occupied_orbital_coeffs(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], /) -> None: ...

    @property
    def density_matrix(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    @density_matrix.setter
    def density_matrix(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], /) -> None: ...

    @property
    def orbital_energies(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]: ...

    @orbital_energies.setter
    def orbital_energies(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')], /) -> None: ...

    def expectation_value(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], /) -> float: ...

    def __repr__(self) -> str: ...

class Wavefunction:
    @property
    def molecular_orbitals(self) -> MolecularOrbitals: ...

    @molecular_orbitals.setter
    def molecular_orbitals(self, arg: MolecularOrbitals, /) -> None: ...

    @property
    def atoms(self) -> list[Atom]: ...

    def mulliken_charges(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]: ...

    def multiplicity(self) -> int: ...

    def copy(self) -> Wavefunction: ...

    def rotate(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')], /) -> None: ...

    def translate(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], /) -> None: ...

    def transform(self, arg0: Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')], arg1: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], /) -> None: ...

    def charge(self) -> int: ...

    @staticmethod
    def load(arg: str, /) -> Wavefunction: ...

    def save(self, arg: str, /) -> bool: ...

    @property
    def basis(self) -> AOBasis: ...

    def electron_density(self, points: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], derivatives: int = 0) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def chelpg_charges(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]: ...

    def to_fchk(self, arg: str, /) -> None: ...

    @staticmethod
    def from_fchk(arg: str, /) -> Wavefunction: ...

    @staticmethod
    def from_molden(arg: str, /) -> Wavefunction: ...

    def __repr__(self) -> str: ...

class SCFConvergenceSettings:
    def __init__(self) -> None: ...

    @property
    def energy_threshold(self) -> float: ...

    @energy_threshold.setter
    def energy_threshold(self, arg: float, /) -> None: ...

    @property
    def commutator_threshold(self) -> float: ...

    @commutator_threshold.setter
    def commutator_threshold(self, arg: float, /) -> None: ...

    @property
    def incremental_fock_threshold(self) -> float: ...

    @incremental_fock_threshold.setter
    def incremental_fock_threshold(self, arg: float, /) -> None: ...

    def energy_converged(self, arg: float, /) -> bool: ...

    def commutator_converged(self, arg: float, /) -> bool: ...

    def energy_and_commutator_converged(self, arg0: float, arg1: float, /) -> bool: ...

    def start_incremental_fock(self, arg: float, /) -> bool: ...

class HF:
    @overload
    def __init__(self, arg: HartreeFock, /) -> None: ...

    @overload
    def __init__(self, arg0: HartreeFock, arg1: SpinorbitalKind, /) -> None: ...

    @property
    def convergence_settings(self) -> SCFConvergenceSettings: ...

    @convergence_settings.setter
    def convergence_settings(self, arg: SCFConvergenceSettings, /) -> None: ...

    def set_charge_multiplicity(self, arg0: int, arg1: int, /) -> None: ...

    def set_initial_guess(self, arg: Wavefunction, /) -> None: ...

    def scf_kind(self) -> str: ...

    def run(self) -> float: ...

    def compute_scf_energy(self) -> float: ...

    def wavefunction(self) -> Wavefunction: ...

    def __repr__(self) -> str: ...

class HartreeFock:
    def __init__(self, arg: AOBasis, /) -> None: ...

    def point_charge_interaction_energy(self, arg: Sequence[PointCharge], /) -> float: ...

    def wolf_point_charge_interaction_energy(self, arg0: Sequence[PointCharge], arg1: Sequence[float], arg2: float, arg3: float, /) -> float: ...

    def point_charge_interaction_matrix(self, point_charges: Sequence[PointCharge], alpha: float = 1e+16) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def wolf_interaction_matrix(self, arg0: Sequence[PointCharge], arg1: Sequence[float], arg2: float, arg3: float, /) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    @overload
    def nuclear_attraction_matrix(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    @overload
    def nuclear_attraction_matrix(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def nuclear_electric_field_contribution(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], /) -> Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')]: ...

    def electronic_electric_field_contribution(self, arg0: MolecularOrbitals, arg1: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], /) -> Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')]: ...

    def nuclear_electric_potential_contribution(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], /) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]: ...

    def electronic_electric_potential_contribution(self, arg0: MolecularOrbitals, arg1: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], /) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]: ...

    def set_density_fitting_basis(self, arg: str, /) -> None: ...

    def kinetic_matrix(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def overlap_matrix(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def overlap_matrix_for_basis(self, arg: AOBasis, /) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def nuclear_repulsion(self) -> float: ...

    def scf(self, unrestricted: SpinorbitalKind = SpinorbitalKind.Restricted) -> HF: ...

    def set_precision(self, arg: float, /) -> None: ...

    def coulomb_matrix(self, arg: MolecularOrbitals, /) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def coulomb_and_exchange_matrices(self, arg: MolecularOrbitals, /) -> JKPair: ...

    def fock_matrix(self, arg: MolecularOrbitals, /) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def compute_gradient(self, mo: MolecularOrbitals) -> Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')]:
        """Compute atomic gradients for the given molecular orbitals"""

    def nuclear_repulsion_gradient(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')]:
        """Compute nuclear repulsion gradient"""

    def hessian_evaluator(self) -> HessianEvaluatorHF:
        """Create a Hessian evaluator for this HF object"""

    def __repr__(self) -> str: ...

class HessianEvaluatorHF:
    def __init__(self, hf: HartreeFock) -> None: ...

    def set_method(self, method: "occ::qm::HessianEvaluator<occ::qm::HartreeFock>::Method") -> None: ...

    def set_step_size(self, h: float) -> None:
        """Set finite differences step size in Bohr"""

    def set_use_acoustic_sum_rule(self, use: bool) -> None:
        """Enable/disable acoustic sum rule optimization"""

    def step_size(self) -> float:
        """Get current step size"""

    def use_acoustic_sum_rule(self) -> bool:
        """Check if acoustic sum rule is enabled"""

    def nuclear_repulsion(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]:
        """Compute nuclear repulsion Hessian"""

    def __call__(self, mo: Wavefunction) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]:
        """Compute the full molecular Hessian"""

    def __repr__(self) -> str: ...

class VibrationalModes:
    @property
    def frequencies_cm(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]:
        """Frequencies in cm⁻¹"""

    @property
    def frequencies_hartree(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]:
        """Frequencies in Hartree"""

    @property
    def normal_modes(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]:
        """Normal mode vectors (3N×3N)"""

    @property
    def mass_weighted_hessian(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]:
        """Mass-weighted Hessian matrix"""

    @property
    def hessian(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]:
        """Original Hessian matrix"""

    def n_modes(self) -> int:
        """Number of vibrational modes"""

    def n_atoms(self) -> int:
        """Number of atoms"""

    def summary_string(self) -> str:
        """Get formatted summary of vibrational analysis"""

    def frequencies_string(self) -> str:
        """Get formatted frequency table"""

    def normal_modes_string(self, threshold: float = 0.1) -> str:
        """Get formatted normal mode vectors"""

    def get_all_frequencies(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]:
        """Get all frequencies as a sorted vector"""

    def __repr__(self) -> str: ...

@overload
def compute_vibrational_modes(hessian: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], masses: Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')], positions: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')] = ..., project_tr_rot: bool = False) -> VibrationalModes:
    """Compute vibrational modes from Hessian matrix"""

@overload
def compute_vibrational_modes(hessian: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], molecule: Molecule, project_tr_rot: bool = False) -> VibrationalModes:
    """Compute vibrational modes from Hessian matrix and molecule"""

@overload
def mass_weighted_hessian(hessian: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], masses: Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]:
    """Construct mass-weighted Hessian matrix"""

@overload
def mass_weighted_hessian(hessian: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], molecule: Molecule) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]:
    """Construct mass-weighted Hessian matrix from molecule"""

def eigenvalues_to_frequencies_cm(eigenvalues: Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]:
    """Convert eigenvalues to frequencies in cm⁻¹"""

def frequencies_cm_to_hartree(frequencies_cm: Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]:
    """Convert frequencies from cm⁻¹ to Hartree"""

class JKPair:
    def __init__(self) -> None: ...

    @property
    def J(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    @J.setter
    def J(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], /) -> None: ...

    @property
    def K(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    @K.setter
    def K(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], /) -> None: ...

class JKTriple:
    def __init__(self) -> None: ...

    @property
    def J(self) -> MatTriple: ...

    @J.setter
    def J(self, arg: MatTriple, /) -> None: ...

    @property
    def K(self) -> MatTriple: ...

    @K.setter
    def K(self, arg: MatTriple, /) -> None: ...

class Operator(enum.Enum):
    Overlap = 0

    Nuclear = 1

    Kinetic = 2

    Coulomb = 3

    Dipole = 4

    Quadrupole = 5

    Octapole = 6

    Hexadecapole = 7

    Rinv = 8

class IntegralEngine:
    @overload
    def __init__(self, arg: AOBasis, /) -> None: ...

    @overload
    def __init__(self, arg0: Sequence[Atom], arg1: Sequence[Shell], /) -> None: ...

    def schwarz(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def set_precision(self, arg: float, /) -> None: ...

    def set_range_separated_omega(self, arg: float, /) -> None: ...

    def range_separated_omega(self) -> float: ...

    def is_spherical(self) -> bool: ...

    def have_auxiliary_basis(self) -> bool: ...

    def set_auxiliary_basis(self, basis: Sequence[Shell], dummy: bool = False) -> None: ...

    def clear_auxiliary_basis(self) -> None: ...

    def one_electron_operator(self, operator: Operator, use_shellpair_list: bool = True) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def coulomb(self, kind: SpinorbitalKind, mo: MolecularOrbitals, schwarz: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')] = ...) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def coulomb_and_exchange(self, kind: SpinorbitalKind, mo: MolecularOrbitals, schwarz: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')] = ...) -> JKPair: ...

    def fock_operator(self, kind: SpinorbitalKind, mo: MolecularOrbitals, schwarz: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')] = ...) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def point_charge_potential(self, charges: Sequence[PointCharge], alpha: float = 1e+16) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def electric_potential(self, arg0: MolecularOrbitals, arg1: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], /) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]: ...

    def multipole(self, order: int, mo: MolecularOrbitals, origin: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')] = ...) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]: ...

    def nbf(self) -> int: ...

    def nsh(self) -> int: ...

    def aobasis(self) -> AOBasis: ...

    def auxbasis(self) -> AOBasis: ...

    def nbf_aux(self) -> int: ...

    def nsh_aux(self) -> int: ...

    def one_electron_operator_grad(self, operator: Operator, use_shellpair_list: bool = True) -> MatTriple: ...

    def fock_operator_grad(self, kind: SpinorbitalKind, mo: MolecularOrbitals, schwarz: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')] = ...) -> MatTriple: ...

    def coulomb_grad(self, kind: SpinorbitalKind, mo: MolecularOrbitals, schwarz: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')] = ...) -> MatTriple: ...

    def coulomb_exchange_grad(self, kind: SpinorbitalKind, mo: MolecularOrbitals, schwarz: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')] = ...) -> JKTriple: ...

    def fock_operator_mixed_basis(self, density_matrix: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], density_basis: AOBasis, is_shell_diagonal: bool) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def coulomb_list(self, kind: SpinorbitalKind, molecular_orbitals: Sequence[MolecularOrbitals], schwarz: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')] = ...) -> list[Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]]: ...

    def coulomb_and_exchange_list(self, kind: SpinorbitalKind, molecular_orbitals: Sequence[MolecularOrbitals], schwarz: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')] = ...) -> list[JKPair]: ...

    def effective_core_potential(self, use_shellpair_list: bool = True) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def have_effective_core_potentials(self) -> bool: ...

    def set_effective_core_potentials(self, ecp_shells: Sequence[Shell], ecp_electrons: Sequence[int]) -> None: ...

    def rinv_operator_atom_center(self, atom_index: int, use_shellpair_list: bool = True) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def rinv_operator_grad_atom(self, atom_index: int, use_shellpair_list: bool = True) -> MatTriple: ...

    def wolf_point_charge_potential(self, charges: Sequence[PointCharge], partial_charges: Sequence[float], alpha: float, cutoff_radius: float) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def __repr__(self) -> str: ...

class OrbitalSmearingKind(enum.Enum):
    None = 0

    Fermi = 1

    Gaussian = 2

    Linear = 3

class OrbitalSmearing:
    def __init__(self) -> None: ...

    @property
    def kind(self) -> OrbitalSmearingKind: ...

    @kind.setter
    def kind(self, arg: OrbitalSmearingKind, /) -> None: ...

    @property
    def mu(self) -> float: ...

    @mu.setter
    def mu(self, arg: float, /) -> None: ...

    @property
    def fermi_level(self) -> float: ...

    @fermi_level.setter
    def fermi_level(self, arg: float, /) -> None: ...

    @property
    def sigma(self) -> float: ...

    @sigma.setter
    def sigma(self, arg: float, /) -> None: ...

    @property
    def entropy(self) -> float: ...

    @entropy.setter
    def entropy(self, arg: float, /) -> None: ...

    def smear_orbitals(self, arg: MolecularOrbitals, /) -> None: ...

    def calculate_entropy(self, arg: MolecularOrbitals, /) -> float: ...

    def ec_entropy(self) -> float: ...

    def calculate_fermi_occupations(self, arg: MolecularOrbitals, /) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]: ...

    def calculate_gaussian_occupations(self, arg: MolecularOrbitals, /) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]: ...

    def calculate_linear_occupations(self, arg: MolecularOrbitals, /) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]: ...

    def __repr__(self) -> str: ...

class IntegralEngineDFPolicy(enum.Enum):
    Choose = 0

    Direct = 1

    Stored = 2

class IntegralEngineDF:
    def __init__(self, arg0: Sequence[Atom], arg1: Sequence[Shell], arg2: Sequence[Shell], /) -> None: ...

    def exchange(self, arg: MolecularOrbitals, /) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def coulomb(self, arg: MolecularOrbitals, /) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def coulomb_and_exchange(self, arg: MolecularOrbitals, /) -> JKPair: ...

    def fock_operator(self, arg: MolecularOrbitals, /) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def set_integral_policy(self, arg: IntegralEngineDFPolicy, /) -> None: ...

    def set_range_separated_omega(self, arg: float, /) -> None: ...

    def set_precision(self, arg: float, /) -> None: ...

    def __repr__(self) -> str: ...

class GTOValues:
    def __init__(self) -> None: ...

    def reserve(self, arg0: int, arg1: int, arg2: int, /) -> None: ...

    def set_zero(self) -> None: ...

    @property
    def phi(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    @phi.setter
    def phi(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], /) -> None: ...

    @property
    def phi_x(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    @phi_x.setter
    def phi_x(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], /) -> None: ...

    @property
    def phi_y(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    @phi_y.setter
    def phi_y(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], /) -> None: ...

    @property
    def phi_z(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    @phi_z.setter
    def phi_z(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], /) -> None: ...

    @property
    def phi_xx(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    @phi_xx.setter
    def phi_xx(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], /) -> None: ...

    @property
    def phi_xy(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    @phi_xy.setter
    def phi_xy(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], /) -> None: ...

    @property
    def phi_xz(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    @phi_xz.setter
    def phi_xz(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], /) -> None: ...

    @property
    def phi_yy(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    @phi_yy.setter
    def phi_yy(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], /) -> None: ...

    @property
    def phi_yz(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    @phi_yz.setter
    def phi_yz(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], /) -> None: ...

    @property
    def phi_zz(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    @phi_zz.setter
    def phi_zz(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')], /) -> None: ...

class GridSettings:
    def __init__(self) -> None: ...

    @property
    def max_angular_points(self) -> int: ...

    @max_angular_points.setter
    def max_angular_points(self, arg: int, /) -> None: ...

    @property
    def min_angular_points(self) -> int: ...

    @min_angular_points.setter
    def min_angular_points(self, arg: int, /) -> None: ...

    @property
    def radial_points(self) -> int: ...

    @radial_points.setter
    def radial_points(self, arg: int, /) -> None: ...

    @property
    def radial_precision(self) -> float: ...

    @radial_precision.setter
    def radial_precision(self, arg: float, /) -> None: ...

    def __repr__(self) -> str: ...

class KS:
    @overload
    def __init__(self, arg: DFT, /) -> None: ...

    @overload
    def __init__(self, arg0: DFT, arg1: SpinorbitalKind, /) -> None: ...

    @property
    def convergence_settings(self) -> SCFConvergenceSettings: ...

    @convergence_settings.setter
    def convergence_settings(self, arg: SCFConvergenceSettings, /) -> None: ...

    def set_charge_multiplicity(self, arg0: int, arg1: int, /) -> None: ...

    def set_initial_guess(self, arg: Wavefunction, /) -> None: ...

    def scf_kind(self) -> str: ...

    def run(self) -> float: ...

    def compute_scf_energy(self) -> float: ...

    def wavefunction(self) -> Wavefunction: ...

    def __repr__(self) -> str: ...

class DFT:
    @overload
    def __init__(self, arg0: str, arg1: AOBasis, /) -> None: ...

    @overload
    def __init__(self, arg0: str, arg1: AOBasis, arg2: GridSettings, /) -> None: ...

    def nuclear_attraction_matrix(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def kinetic_matrix(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def set_density_fitting_basis(self, arg: str, /) -> None: ...

    def overlap_matrix(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def nuclear_repulsion(self) -> float: ...

    def set_precision(self, arg: float, /) -> None: ...

    def set_method(self, arg: str, /) -> None: ...

    def fock_matrix(self, arg: MolecularOrbitals, /) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]: ...

    def scf(self, unrestricted: SpinorbitalKind = SpinorbitalKind.Restricted) -> KS: ...

    def compute_gradient(self, mo: MolecularOrbitals) -> Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')]:
        """Compute atomic gradients for the given molecular orbitals"""

    def hessian_evaluator(self) -> HessianEvaluatorDFT:
        """Create a Hessian evaluator for this DFT object"""

    def __repr__(self) -> str: ...

class HessianEvaluatorDFT:
    def __init__(self, dft: DFT) -> None: ...

    def set_method(self, method: "occ::qm::HessianEvaluator<occ::dft::DFT>::Method") -> None: ...

    def set_step_size(self, h: float) -> None:
        """Set finite differences step size in Bohr"""

    def set_use_acoustic_sum_rule(self, use: bool) -> None:
        """Enable/disable acoustic sum rule optimization"""

    def step_size(self) -> float:
        """Get current step size"""

    def use_acoustic_sum_rule(self) -> bool:
        """Check if acoustic sum rule is enabled"""

    def nuclear_repulsion(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]:
        """Compute nuclear repulsion Hessian"""

    def __call__(self, mo: Wavefunction) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]:
        """Compute the full molecular Hessian"""

    def __repr__(self) -> str: ...

class Mult:
    @overload
    def __init__(self, max_rank: int) -> None: ...

    @overload
    def __init__(self) -> None: ...

    @property
    def max_rank(self) -> int:
        """maximum rank of multipole moments"""

    @max_rank.setter
    def max_rank(self, arg: int, /) -> None: ...

    @property
    def q(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]:
        """multipole moment coefficients"""

    @q.setter
    def q(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')], /) -> None: ...

    def num_components(self) -> int:
        """total number of multipole components"""

    def to_string(self, lm: int) -> str:
        """string representation of specific multipole component"""

    def get_multipole(self, l: int, m: int) -> float:
        """Get multipole component by quantum numbers (l, m)"""

    def get_component(self, name: str) -> float:
        """Get multipole component by string name (e.g., 'Q21c', 'Q30')"""

    @staticmethod
    def component_name_to_lm(name: str) -> "std::__1::pair<int, int>":
        """Convert component name to (l, m) quantum numbers"""

    def __repr__(self) -> str: ...

class DMASettings:
    def __init__(self) -> None: ...

    @property
    def max_rank(self) -> int:
        """maximum multipole rank"""

    @max_rank.setter
    def max_rank(self, arg: int, /) -> None: ...

    @property
    def big_exponent(self) -> float:
        """large exponent threshold for analytical integration"""

    @big_exponent.setter
    def big_exponent(self, arg: float, /) -> None: ...

    @property
    def include_nuclei(self) -> bool:
        """include nuclear contributions to multipoles"""

    @include_nuclei.setter
    def include_nuclei(self, arg: bool, /) -> None: ...

    def __repr__(self) -> str: ...

class DMAResult:
    def __init__(self) -> None: ...

    @property
    def max_rank(self) -> int:
        """maximum multipole rank"""

    @max_rank.setter
    def max_rank(self, arg: int, /) -> None: ...

    @property
    def multipoles(self) -> list[Mult]:
        """multipole moments for each site"""

    @multipoles.setter
    def multipoles(self, arg: Sequence[Mult], /) -> None: ...

    def __repr__(self) -> str: ...

class DMASites:
    def __init__(self) -> None: ...

    def size(self) -> int:
        """number of sites"""

    def num_atoms(self) -> int:
        """number of atoms"""

    @property
    def atoms(self) -> list[Atom]:
        """atom information"""

    @atoms.setter
    def atoms(self, arg: Sequence[Atom], /) -> None: ...

    @property
    def name(self) -> list[str]:
        """site names"""

    @name.setter
    def name(self, arg: Sequence[str], /) -> None: ...

    @property
    def positions(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')]:
        """site positions"""

    @positions.setter
    def positions(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(3, None), order='F')], /) -> None: ...

    @property
    def atom_indices(self) -> Annotated[NDArray[numpy.int32], dict(shape=(None,), order='C')]:
        """atom indices for sites"""

    @atom_indices.setter
    def atom_indices(self, arg: Annotated[NDArray[numpy.int32], dict(shape=(None,), order='C')], /) -> None: ...

    @property
    def radii(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]:
        """site radii"""

    @radii.setter
    def radii(self, arg: Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')], /) -> None: ...

    @property
    def limits(self) -> Annotated[NDArray[numpy.int32], dict(shape=(None,), order='C')]:
        """multipole rank limits per site"""

    @limits.setter
    def limits(self, arg: Annotated[NDArray[numpy.int32], dict(shape=(None,), order='C')], /) -> None: ...

    def __repr__(self) -> str: ...

class DMACalculator:
    def __init__(self, wavefunction: Wavefunction) -> None: ...

    def update_settings(self, settings: DMASettings) -> None:
        """update DMA calculation settings"""

    def settings(self) -> DMASettings:
        """get current settings"""

    def set_radius_for_element(self, atomic_number: int, radius_angs: float) -> None:
        """set site radius for specific element"""

    def set_limit_for_element(self, atomic_number: int, limit: int) -> None:
        """set multipole rank limit for specific element"""

    def sites(self) -> DMASites:
        """get DMA sites information"""

    def compute_multipoles(self) -> DMAResult:
        """compute distributed multipole moments"""

    def compute_total_multipoles(self, result: DMAResult) -> Mult:
        """compute total multipole moments from DMA result"""

    def __repr__(self) -> str: ...

class LinearDMASettings:
    def __init__(self) -> None: ...

    @property
    def max_rank(self) -> int:
        """maximum multipole rank"""

    @max_rank.setter
    def max_rank(self, arg: int, /) -> None: ...

    @property
    def include_nuclei(self) -> bool:
        """include nuclear contributions"""

    @include_nuclei.setter
    def include_nuclei(self, arg: bool, /) -> None: ...

    @property
    def use_slices(self) -> bool:
        """use slice-based integration"""

    @use_slices.setter
    def use_slices(self, arg: bool, /) -> None: ...

    @property
    def tolerance(self) -> float:
        """numerical significance threshold"""

    @tolerance.setter
    def tolerance(self, arg: float, /) -> None: ...

    @property
    def default_radius(self) -> float:
        """default site radius in Angstrom"""

    @default_radius.setter
    def default_radius(self, arg: float, /) -> None: ...

    @property
    def hydrogen_radius(self) -> float:
        """hydrogen site radius in Angstrom"""

    @hydrogen_radius.setter
    def hydrogen_radius(self, arg: float, /) -> None: ...

    def __repr__(self) -> str: ...

class LinearMultipoleCalculator:
    def __init__(self, wavefunction: Wavefunction, settings: LinearDMASettings = ...) -> None: ...

    def calculate(self) -> list[Mult]:
        """calculate multipole moments for linear molecule"""

    def __repr__(self) -> str: ...

class DMAConfig:
    def __init__(self) -> None: ...

    @property
    def wavefunction_filename(self) -> str:
        """path to wavefunction file"""

    @wavefunction_filename.setter
    def wavefunction_filename(self, arg: str, /) -> None: ...

    @property
    def punch_filename(self) -> str:
        """path to punch file output (default: dma.punch)"""

    @punch_filename.setter
    def punch_filename(self, arg: str, /) -> None: ...

    @property
    def settings(self) -> DMASettings:
        """DMA calculation settings"""

    @settings.setter
    def settings(self, arg: DMASettings, /) -> None: ...

    @property
    def atom_radii(self) -> "ankerl::unordered_dense::v4_5_0::detail::table<std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>, double, ankerl::unordered_dense::v4_5_0::hash<std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>, void>, std::__1::equal_to<std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>>, std::__1::allocator<std::__1::pair<std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>, double>>, ankerl::unordered_dense::v4_5_0::bucket_type::standard, ankerl::unordered_dense::v4_5_0::detail::default_container_t, false>":
        """atom-specific radii (element symbol -> radius in Angstrom)"""

    @atom_radii.setter
    def atom_radii(self, arg: "ankerl::unordered_dense::v4_5_0::detail::table<std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>, double, ankerl::unordered_dense::v4_5_0::hash<std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>, void>, std::__1::equal_to<std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>>, std::__1::allocator<std::__1::pair<std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>, double>>, ankerl::unordered_dense::v4_5_0::bucket_type::standard, ankerl::unordered_dense::v4_5_0::detail::default_container_t, false>", /) -> None: ...

    @property
    def atom_limits(self) -> "ankerl::unordered_dense::v4_5_0::detail::table<std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>, int, ankerl::unordered_dense::v4_5_0::hash<std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>, void>, std::__1::equal_to<std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>>, std::__1::allocator<std::__1::pair<std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>, int>>, ankerl::unordered_dense::v4_5_0::bucket_type::standard, ankerl::unordered_dense::v4_5_0::detail::default_container_t, false>":
        """atom-specific max ranks (element symbol -> max rank)"""

    @atom_limits.setter
    def atom_limits(self, arg: "ankerl::unordered_dense::v4_5_0::detail::table<std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>, int, ankerl::unordered_dense::v4_5_0::hash<std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>, void>, std::__1::equal_to<std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>>, std::__1::allocator<std::__1::pair<std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>, int>>, ankerl::unordered_dense::v4_5_0::bucket_type::standard, ankerl::unordered_dense::v4_5_0::detail::default_container_t, false>", /) -> None: ...

    @property
    def write_punch(self) -> bool:
        """whether to write punch file (default: True)"""

    @write_punch.setter
    def write_punch(self, arg: bool, /) -> None: ...

    def __repr__(self) -> str: ...

class DMAOutput:
    @property
    def result(self) -> DMAResult:
        """DMA calculation result"""

    @result.setter
    def result(self, arg: DMAResult, /) -> None: ...

    @property
    def sites(self) -> DMASites:
        """DMA sites information"""

    @sites.setter
    def sites(self, arg: DMASites, /) -> None: ...

    def __repr__(self) -> str: ...

class DMADriver:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, config: DMAConfig) -> None: ...

    def set_config(self, config: DMAConfig) -> None:
        """set DMA configuration"""

    def config(self) -> DMAConfig:
        """get current configuration"""

    @overload
    def run(self) -> DMAOutput:
        """run DMA calculation loading wavefunction from file"""

    @overload
    def run(self, wavefunction: Wavefunction) -> DMAOutput:
        """run DMA calculation with provided wavefunction"""

    @staticmethod
    def generate_punch_file(result: DMAResult, sites: DMASites) -> str:
        """generate punch file content as string"""

    @staticmethod
    def write_punch_file(filename: str, result: DMAResult, sites: DMASites) -> None:
        """write punch file to disk"""

    def __repr__(self) -> str: ...

def generate_punch_file(result: DMAResult, sites: DMASites) -> str:
    """Generate GDMA-compatible punch file content from DMA results"""

def write_punch_file(filename: str, result: DMAResult, sites: DMASites) -> None:
    """Write GDMA-compatible punch file from DMA results"""

class SurfaceKind(enum.Enum):
    PromoleculeDensity = 0

    Hirshfeld = 1

    EEQ_ESP = 2

    ElectronDensity = 3

    ESP = 4

    SpinDensity = 5

    DeformationDensity = 6

    Orbital = 7

    CrystalVoid = 8

class PropertyKind(enum.Enum):
    Dnorm = 0

    Dint_norm = 1

    Dext_norm = 2

    Dint = 3

    Dext = 4

    FragmentPatch = 5

    ShapeIndex = 6

    Curvedness = 7

    EEQ_ESP = 8

    PromoleculeDensity = 9

    ESP = 10

    ElectronDensity = 11

    SpinDensity = 12

    DeformationDensity = 13

    Orbital = 14

class IsosurfaceProperties:
    def __init__(self) -> None: ...

    @overload
    def add(self, arg0: str, arg1: Annotated[NDArray[numpy.float32], dict(shape=(None,), order='C')], /) -> None:
        """Add float property"""

    @overload
    def add(self, arg0: str, arg1: Annotated[NDArray[numpy.int32], dict(shape=(None,), order='C')], /) -> None:
        """Add integer property"""

    def has_property(self, arg: str, /) -> bool: ...

    def get_float(self, arg: str, /) -> object:
        """Get float property"""

    def get_int(self, arg: str, /) -> object:
        """Get integer property"""

    def merge(self, arg: IsosurfaceProperties, /) -> None: ...

    def count(self) -> int: ...

class Isosurface:
    def __init__(self) -> None: ...

    @property
    def vertices(self) -> Annotated[NDArray[numpy.float32], dict(shape=(3, None), order='F')]: ...

    @vertices.setter
    def vertices(self, arg: Annotated[NDArray[numpy.float32], dict(shape=(3, None), order='F')], /) -> None: ...

    @property
    def faces(self) -> Annotated[NDArray[numpy.int32], dict(shape=(3, None), order='F')]: ...

    @faces.setter
    def faces(self, arg: Annotated[NDArray[numpy.int32], dict(shape=(3, None), order='F')], /) -> None: ...

    @property
    def normals(self) -> Annotated[NDArray[numpy.float32], dict(shape=(3, None), order='F')]: ...

    @normals.setter
    def normals(self, arg: Annotated[NDArray[numpy.float32], dict(shape=(3, None), order='F')], /) -> None: ...

    @property
    def gaussian_curvature(self) -> Annotated[NDArray[numpy.float32], dict(shape=(None,), order='C')]: ...

    @gaussian_curvature.setter
    def gaussian_curvature(self, arg: Annotated[NDArray[numpy.float32], dict(shape=(None,), order='C')], /) -> None: ...

    @property
    def mean_curvature(self) -> Annotated[NDArray[numpy.float32], dict(shape=(None,), order='C')]: ...

    @mean_curvature.setter
    def mean_curvature(self, arg: Annotated[NDArray[numpy.float32], dict(shape=(None,), order='C')], /) -> None: ...

    @property
    def properties(self) -> IsosurfaceProperties: ...

    @properties.setter
    def properties(self, arg: IsosurfaceProperties, /) -> None: ...

    def save(self, filename: str, binary: bool = True) -> None: ...

class IsosurfaceGenerationParameters:
    def __init__(self) -> None: ...

    @property
    def isovalue(self) -> float: ...

    @isovalue.setter
    def isovalue(self, arg: float, /) -> None: ...

    @property
    def separation(self) -> float: ...

    @separation.setter
    def separation(self, arg: float, /) -> None: ...

    @property
    def background_density(self) -> float: ...

    @background_density.setter
    def background_density(self, arg: float, /) -> None: ...

    @property
    def surface_orbital_index(self) -> "occ::isosurface::OrbitalIndex": ...

    @surface_orbital_index.setter
    def surface_orbital_index(self, arg: "occ::isosurface::OrbitalIndex", /) -> None: ...

    @property
    def property_orbital_indices(self) -> list["occ::isosurface::OrbitalIndex"]: ...

    @property_orbital_indices.setter
    def property_orbital_indices(self, arg: Sequence["occ::isosurface::OrbitalIndex"], /) -> None: ...

    @property
    def flip_normals(self) -> bool: ...

    @flip_normals.setter
    def flip_normals(self, arg: bool, /) -> None: ...

    @property
    def binary_output(self) -> bool: ...

    @binary_output.setter
    def binary_output(self, arg: bool, /) -> None: ...

    @property
    def surface_kind(self) -> SurfaceKind: ...

    @surface_kind.setter
    def surface_kind(self, arg: SurfaceKind, /) -> None: ...

    @property
    def properties(self) -> list[PropertyKind]: ...

    @properties.setter
    def properties(self, arg: Sequence[PropertyKind], /) -> None: ...

class IsosurfaceCalculator:
    def __init__(self) -> None: ...

    def set_molecule(self, arg: Molecule, /) -> None: ...

    def set_environment(self, arg: Molecule, /) -> None: ...

    def set_wavefunction(self, arg: Wavefunction, /) -> None: ...

    def set_crystal(self, arg: Crystal, /) -> None: ...

    def set_parameters(self, arg: IsosurfaceGenerationParameters, /) -> None: ...

    def validate(self) -> bool: ...

    def compute(self) -> None: ...

    def compute_surface_property(self, arg: PropertyKind, /) -> Annotated[NDArray[numpy.float32], dict(shape=(None,), order='C')]: ...

    def isosurface(self) -> Isosurface: ...

    def requires_crystal(self) -> bool: ...

    def requires_wavefunction(self) -> bool: ...

    def requires_environment(self) -> bool: ...

    def have_crystal(self) -> bool: ...

    def have_wavefunction(self) -> bool: ...

    def have_environment(self) -> bool: ...

    def error_message(self) -> str: ...

class ElectronDensityFunctor:
    def __init__(self, wavefunction: Wavefunction, mo_index: int = 1) -> None: ...

    @property
    def orbital_index(self) -> int: ...

    @orbital_index.setter
    def orbital_index(self, arg: int, /) -> None: ...

    def __call__(self, arg: Annotated[NDArray[numpy.float32], dict(shape=(3, None), order='F')], /) -> Annotated[NDArray[numpy.float32], dict(shape=(None,), order='C')]: ...

    def num_calls(self) -> int: ...

class ElectricPotentialFunctor:
    def __init__(self, wavefunction: Wavefunction) -> None: ...

    def __call__(self, arg: Annotated[NDArray[numpy.float32], dict(shape=(3, None), order='F')], /) -> Annotated[NDArray[numpy.float32], dict(shape=(None,), order='C')]: ...

    def num_calls(self) -> int: ...

class ElectricPotentialFunctorPC:
    def __init__(self, molecule: Molecule) -> None: ...

    def __call__(self, arg: Annotated[NDArray[numpy.float32], dict(shape=(3, None), order='F')], /) -> Annotated[NDArray[numpy.float32], dict(shape=(None,), order='C')]: ...

    def num_calls(self) -> int: ...

class VolumePropertyKind(enum.Enum):
    ElectronDensity = 0

    ElectronDensityAlpha = 1

    ElectronDensityBeta = 2

    ElectricPotential = 3

    EEQ_ESP = 4

    PromoleculeDensity = 5

    DeformationDensity = 6

    XCDensity = 7

    CrystalVoid = 8

class SpinConstraint(enum.Enum):
    Total = 0

    Alpha = 1

    Beta = 2

class VolumeGenerationParameters:
    def __init__(self) -> None: ...

    @property
    def property(self) -> VolumePropertyKind: ...

    @property.setter
    def property(self, arg: VolumePropertyKind, /) -> None: ...

    @property
    def spin(self) -> SpinConstraint: ...

    @spin.setter
    def spin(self, arg: SpinConstraint, /) -> None: ...

    @property
    def functional(self) -> str: ...

    @functional.setter
    def functional(self, arg: str, /) -> None: ...

    @property
    def mo_number(self) -> int: ...

    @mo_number.setter
    def mo_number(self, arg: int, /) -> None: ...

    @property
    def steps(self) -> list[int]: ...

    @steps.setter
    def steps(self, arg: Sequence[int], /) -> None: ...

    @property
    def da(self) -> list[float]: ...

    @da.setter
    def da(self, arg: Sequence[float], /) -> None: ...

    @property
    def db(self) -> list[float]: ...

    @db.setter
    def db(self, arg: Sequence[float], /) -> None: ...

    @property
    def dc(self) -> list[float]: ...

    @dc.setter
    def dc(self, arg: Sequence[float], /) -> None: ...

    @property
    def origin(self) -> list[float]: ...

    @origin.setter
    def origin(self, arg: Sequence[float], /) -> None: ...

    @property
    def adaptive_bounds(self) -> bool: ...

    @adaptive_bounds.setter
    def adaptive_bounds(self, arg: bool, /) -> None: ...

    @property
    def value_threshold(self) -> float: ...

    @value_threshold.setter
    def value_threshold(self, arg: float, /) -> None: ...

    @property
    def buffer_distance(self) -> float: ...

    @buffer_distance.setter
    def buffer_distance(self, arg: float, /) -> None: ...

    @property
    def crystal_filename(self) -> str: ...

    @crystal_filename.setter
    def crystal_filename(self, arg: str, /) -> None: ...

class VolumeData:
    @property
    def name(self) -> str: ...

    @property
    def property(self) -> VolumePropertyKind: ...

    def nx(self) -> int: ...

    def ny(self) -> int: ...

    def nz(self) -> int: ...

    def total_points(self) -> int: ...

    @property
    def origin(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]: ...

    @property
    def basis(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')]: ...

    @property
    def steps(self) -> Annotated[NDArray[numpy.int32], dict(shape=(3), order='C')]: ...

    def get_data(self) -> list[float]:
        """
        Get volume data as flattened vector (use reshape((nx, ny, nz)) in Python)
        """

class VolumeCalculator:
    def __init__(self) -> None: ...

    def set_wavefunction(self, arg: Wavefunction, /) -> None: ...

    def set_molecule(self, arg: Molecule, /) -> None: ...

    def compute_volume(self, arg: VolumeGenerationParameters, /) -> VolumeData: ...

    def volume_as_cube_string(self, arg: VolumeData, /) -> str: ...

    @staticmethod
    def compute_density_volume(arg0: Wavefunction, arg1: VolumeGenerationParameters, /) -> VolumeData: ...

    @staticmethod
    def compute_mo_volume(arg0: Wavefunction, arg1: int, arg2: VolumeGenerationParameters, /) -> VolumeData: ...

def generate_electron_density_cube(wavefunction: Wavefunction, nx: int, ny: int, nz: int) -> str:
    """Generate electron density cube file as string"""

def generate_mo_cube(wavefunction: Wavefunction, mo_index: int, nx: int, ny: int, nz: int) -> str:
    """Generate molecular orbital cube file as string"""

def generate_esp_cube(wavefunction: Wavefunction, nx: int, ny: int, nz: int) -> str:
    """Generate electrostatic potential cube file as string"""

class CEParameterizedModel:
    def ce_model_from_string(self) -> CEParameterizedModel: ...

class CEEnergyComponents:
    def coulomb_kjmol(self) -> float: ...

    def exchange_repulsion_kjmol(self) -> float: ...

    def polarization_kjmol(self) -> float: ...

    def dispersion_kjmol(self) -> float: ...

    def repulsion_kjmol(self) -> float: ...

    def exchange_kjmol(self) -> float: ...

    def total_kjmol(self) -> float: ...

    def __add__(self, arg: CEEnergyComponents, /) -> CEEnergyComponents: ...

    def __sub__(self, arg: CEEnergyComponents, /) -> CEEnergyComponents: ...

    def __iadd__(self, arg: CEEnergyComponents, /) -> None: ...

    def __isub__(self, arg: CEEnergyComponents, /) -> None: ...

class CEModelInteraction:
    def __init__(self, arg: CEParameterizedModel, /) -> None: ...

    def __call__(self, arg0: Wavefunction, arg1: Wavefunction, /) -> CEEnergyComponents: ...

class TransformResult:
    @property
    def rotation(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')]: ...

    @property
    def translation(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]: ...

    @property
    def wfn(self) -> Wavefunction: ...

    @property
    def rmsd(self) -> float: ...

class WavefunctionTransformer:
    def calculate_transform(self, arg0: Molecule, arg1: Crystal, /) -> TransformResult: ...

def set_log_file(arg: str, /) -> None: ...

def set_num_threads(arg: int, /) -> None: ...

def set_data_directory(arg: str, /) -> None: ...

def calculate_crystal_growth_energies(arg: CrystalGrowthConfig, /) -> CrystalGrowthResult: ...
