"""ResidueList data structure."""

import csv
import logging
from os import PathLike
from typing import Any

try:
    from typing import Self  # type: ignore
except ImportError:
    from typing_extensions import Self

from residuum.residue import Residue

LOGGER = logging.getLogger(__name__)


class ResidueList:
    """List of amino acid residues."""

    def __init__(self, data: list[Residue]) -> None:
        self._list = [
            item if isinstance(item, Residue) else Residue(dict(**item)) for item in data
        ]

    def __iter__(self):
        return iter(self._list)

    def __getitem__(self, indexer):
        if isinstance(indexer, (int, slice)):
            return self._list[indexer]
        elif isinstance(indexer, tuple):
            if len(indexer) != 3:
                raise ValueError(
                    f"Tuple indexer expected to have 3 elements (name, residue, anchor): {indexer}"
                )
            return self._as_dict()[indexer]
        else:
            raise TypeError(f"Unsupported indexing type: {type(indexer)}")

    def __len__(self) -> int:
        return len(self._list)

    def __repr__(self) -> str:
        residue_repr = "\n".join([f"    {repr(r)}," for r in self._list])
        return f"{self.__class__.__name__}([\n{residue_repr}\n])"

    def __add__(self, other):
        if isinstance(other, ResidueList):
            other_list = other._list
        elif isinstance(other, list):
            other_list = other
        else:
            raise TypeError(f"Unsupported type: {type(other)}")
        return ResidueList(self._list + other_list)

    def _as_dict(self) -> dict[tuple[str, str, str], Residue]:
        """Convert to dictionary with (name, residue, anchor) keys."""
        return {(r.name, r.residue, r.anchor): r for r in self._list}

    @classmethod
    def from_file(cls, filepath: str | PathLike) -> Self:
        """
        Read residues from a CSV file.

        Parameters
        ----------
        filepath
            Path to CSV file containing residue data

        Returns
        -------
        ResidueList
            List of parsed residues

        Examples
        --------
        >>> residues = ResidueList.from_file("modifications.csv")
        >>> len(residues)
        42
        """

        def parse_row(row: dict[str, Any]) -> dict[str, Any]:
            if synonyms := row.get("synonyms"):
                if isinstance(synonyms, str):
                    row["synonyms"] = synonyms.split(";") if synonyms else []
            return row

        with open(filepath, "rt") as file:
            reader = csv.DictReader(file, delimiter=",")
            residues: list[Residue] = [Residue(**parse_row(row)) for row in reader]
        return cls(residues)

    def to_file(self, filepath: str | PathLike) -> None:
        """
        Write residues to a CSV file.

        Parameters
        ----------
        filepath
            Path where CSV file should be written

        Examples
        --------
        >>> residues = ResidueList([...])
        >>> residues.to_file("output.csv")
        """

        def parse_residue(residue: Residue) -> dict[str, str]:
            row: dict[str, Any] = residue.model_dump()
            row["synonyms"] = ";".join(row["synonyms"]) if row["synonyms"] else None
            return row

        with open(filepath, "wt") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=Residue.model_fields,
                delimiter=",",
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows([parse_residue(r) for r in self._list])

    def to_smiles_map(self) -> dict[tuple[str, str, str], str]:
        """Convert to dictionary mapping (label, residue, anchor) to SMILES."""
        return {
            (label, res.residue, res.anchor): res.smiles
            for res in self._list
            for label in res.labels
        }
