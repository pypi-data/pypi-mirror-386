"""Chemical composition and formula utilities."""

import re
from collections import Counter

from pyteomics import mass
from rdkit import Chem

H2O_COMPOSITION = mass.Composition({"H": 2, "O": 1})
H2O_MASS = H2O_COMPOSITION.mass()
H_COMPOSITION = mass.Composition({"H": 1})
H_MASS = H_COMPOSITION.mass()


def from_molecule(mol: Chem.Mol) -> mass.Composition:
    """Convert an RDKit molecule object to a pyteomics composition object."""
    atom_counts: Counter[str] = Counter([atom.GetSymbol() for atom in Chem.AddHs(mol).GetAtoms()])
    _ = atom_counts.pop("*", None)
    return mass.Composition(atom_counts)


def to_chemforma(composition: mass.Composition) -> str:
    """
    Convert a pyteomics composition object to a chemForma formula string.

    Parameters
    ----------
    composition
        Chemical composition to convert

    Returns
    -------
    str
        ChemForma formatted string
    """
    parsed_elements = [(_parse_element(elem), count) for elem, count in composition.items()]

    c = [(elem, isotope, count) for (elem, isotope), count in parsed_elements if elem == "C"]
    h = [(elem, isotope, count) for (elem, isotope), count in parsed_elements if elem == "H"]
    other = [
        (elem, isotope, count)
        for (elem, isotope), count in parsed_elements
        if elem not in {"C", "H"}
    ]

    other.sort(key=lambda x: x[0])
    ordered_elements = c + h + other

    formula_parts = [
        f"[{isotope}{elem}{count if count != 1 else ''}]"
        if isotope
        else f"{elem}{count if count != 1 else ''}"
        for elem, isotope, count in ordered_elements
    ]

    return "".join(formula_parts)


def _parse_element(element: str) -> tuple[str, int | None]:
    """Parse an element string into the element name and isotope number."""
    match = re.match(r"([A-Z][a-z]*)(\[\d+\])?", element)
    if match:
        elem, isotope = match.groups()
        isotope = int(isotope.strip("[]")) if isotope else None
        return (elem, isotope)
    return (element, None)


def _composition__repr__(self: mass.Composition) -> str:
    """Custom repr for Composition objects."""
    return "{}({})".format(type(self).__name__, dict.__repr__(self))


mass.Composition.__repr__ = _composition__repr__  # type: ignore
mass.Composition.__str__ = to_chemforma  # type: ignore
