"""Residue data model."""

import logging
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator
from pyteomics import mass, proforma
from rdkit import Chem

from residuum import _composition, molecule
from residuum._databases import (
    get_psi_mod_entry,
    get_unimod_entry,
    resolve_psi_mod_accession,
    resolve_unimod_accession,
)

LOGGER = logging.getLogger(__name__)


class Residue(BaseModel):
    """Amino acid residue with optional modification."""

    name: str
    residue: str
    anchor: Literal["side-chain", "N-term", "C-term"]
    smiles: str
    psi_mod_accession: str | None = None
    unimod_accession: str | None = None
    resid_accession: str | None = None
    chebi_accession: str | None = None
    synonyms: list[str] = []

    model_config = ConfigDict(coerce_numbers_to_str=True)

    def __init__(self, *args, **kwargs):
        """
        Amino acid residue with optional modification.

        Parameters
        ----------
        name
            Name of the residue/modification
        residue
            Single-letter amino acid code for the base residue
        anchor
            How the modification attaches to the residue (``side-chain``, ``N-term``, ``C-term``)
        smiles
            SMILES representation of the complete residue structure
        psi_mod_accession
            PSI-MOD accession number for the modification (optional)
        unimod_accession
            UNIMOD accession number for the modification (optional)
        resid_accession
            RESID accession number (optional)
        chebi_accession
            ChEBI accession number (optional)
        synonyms
            List of synonyms for the residue/modification (optional)

        """
        super().__init__(*args, **kwargs)

    @field_validator("residue")
    def _validate_residue(cls, value):
        if len(value) != 1:
            raise ValueError(f"Invalid residue: {value}")
        if not value.isalpha():
            raise ValueError(f"Invalid residue: {value}")
        return value.upper()

    @field_validator("anchor")
    def _validate_anchor(cls, value):
        if value not in ["side-chain", "N-term", "C-term"]:
            raise ValueError(f"Invalid anchor value: {value}")
        return value

    @field_validator("smiles")
    def _validate_smiles(cls, value):
        if value == "":
            raise ValueError("SMILES cannot be empty")
        # TODO: Actually validate SMILES
        return value

    @field_validator("psi_mod_accession")
    def _validate_psi_mod_accession(cls, value):
        if value == "" or value is None:
            return None
        if value is not None and not value.startswith("MOD:"):
            raise ValueError(f"Invalid PSI-MOD accession: {value}")
        return value

    @field_validator("unimod_accession")
    def _validate_unimod_accession(cls, value):
        if not value:
            return None
        processed_value = value
        if value.startswith("U:"):
            processed_value = value[2:]
        elif value.startswith("UNIMOD:"):
            processed_value = value[7:]
        if not processed_value.isdigit():
            raise ValueError(f"Invalid UNIMOD accession: {value}")
        return processed_value

    @field_validator("resid_accession")
    def _validate_resid_accession(cls, value):
        if not value:
            return None
        if not value.startswith("AA"):
            raise ValueError(f"Invalid RESID accession: {value}")
        return value

    @field_validator("chebi_accession")
    def _validate_chebi_accession(cls, value):
        if not value:
            return None
        if not value.isdigit():
            raise ValueError(f"Invalid ChEBI accession: {value}")
        return value

    @field_validator("synonyms", mode="before")
    def _validate_synonyms(cls, value):
        return value or []

    @property
    def molecule(self) -> Chem.Mol:
        """RDKit molecule object for the residue."""
        mol = Chem.MolFromSmiles(self.smiles)
        if mol is None:
            raise ValueError(f"Invalid SMILES for residue '{self.name}': {self.smiles}")
        return mol

    @property
    def n_terminal_molecule(self) -> Chem.Mol:
        """RDKit molecule with N-terminal asterisk replaced by hydrogen."""
        if self.anchor == "N-term":
            raise ValueError(
                f"Cannot add N-term to residue '{self.name}' with modification on {self.anchor}: "
            )
        return molecule.add_n_terminus(self.molecule)

    @property
    def c_terminal_molecule(self) -> Chem.Mol:
        """RDKit molecule with C-terminal asterisk replaced by hydroxyl group."""
        if self.anchor == "C-term":
            raise ValueError(
                f"Cannot add C-term to residue '{self.name}' with modification on {self.anchor}: "
            )
        return molecule.add_c_terminus(self.molecule)

    @property
    def amino_acid_molecule(self) -> Chem.Mol:
        """RDKit molecule with both terminals replaced to form a complete amino acid."""
        return molecule.to_amino_acid(self.molecule)

    @property
    def composition(self) -> mass.Composition:
        """Chemical composition of the residue."""
        return _composition.from_molecule(self.molecule)

    @property
    def delta_composition(self) -> mass.Composition:
        """
        Chemical composition difference from the unmodified amino acid.

        For terminal modifications, this accounts for the replaced terminus:
        - N-terminal: subtracts H (the N-terminal hydrogen in standard residue)
        - C-terminal: subtracts OH (the C-terminal hydroxyl in standard residue)
        - Side-chain: no adjustment needed
        """
        delta = self.composition - mass.std_aa_comp[self.residue]

        if self.anchor == "N-term":
            # N-terminal modification replaces the N-terminal H
            delta -= mass.Composition({"H": 1})
        elif self.anchor == "C-term":
            # C-terminal modification replaces the C-terminal OH
            delta -= mass.Composition({"H": 1, "O": 1})

        return delta

    @property
    def mass(self) -> float:
        """Mass of the residue in atomic mass units."""
        return self.composition.mass()

    @property
    def delta_mass(self) -> float:
        """
        Mass difference from the unmodified amino acid in atomic mass units.

        For terminal modifications, this accounts for the replaced terminus:
        - N-terminal: subtracts H mass (the N-terminal hydrogen in standard residue)
        - C-terminal: subtracts OH mass (the C-terminal hydroxyl in standard residue)
        - Side-chain: no adjustment needed
        """
        return self.delta_composition.mass()

    @property
    def chemforma(self) -> str:
        """Chemical formula of the residue in chemForma notation."""
        return _composition.to_chemforma(self.composition)

    @property
    def proforma(self) -> str:
        """ProForma representation of the residue."""
        if self.unimod_accession is not None:
            tag = f"[U:{self.unimod_accession}]"
        elif self.psi_mod_accession is not None:
            tag = f"[{self.psi_mod_accession}]"
        elif self.resid_accession is not None:
            tag = f"[R:{self.resid_accession}]"
        else:
            tag = f"[Formula:{self.chemforma}]"

        if self.anchor == "side-chain":
            return f"{self.residue}{tag}"
        elif self.anchor == "N-term":
            return f"{tag}-{self.residue}"
        elif self.anchor == "C-term":
            return f"{self.residue}-{tag}"
        else:
            raise ValueError(f"Invalid anchor value: {self.anchor}")

    @property
    def modification_entry(self) -> dict[str, Any] | None:
        """
        Database entry for the modification.

        Returns Unimod entry if available, otherwise PSI-MOD entry.
        """
        if self.unimod_entry:
            return self.unimod_entry
        return self.psi_mod_entry

    @property
    def unimod_entry(self) -> dict[str, Any] | None:
        """Unimod entry for the modification or None if no Unimod accession."""
        if self.unimod_accession is None:
            return None
        return get_unimod_entry(int(self.unimod_accession))

    @property
    def psi_mod_entry(self) -> dict[str, Any] | None:
        """PSI-MOD entry for the modification or None if no PSI-MOD accession."""
        if self.psi_mod_accession is None:
            return None
        return get_psi_mod_entry(self.psi_mod_accession)

    @property
    def resid_entry(self) -> float | None:
        """Mass from RESID database or None if no RESID accession."""
        raise NotImplementedError

    @property
    def labels(self) -> list[str]:
        """List of all possible labels for the residue."""
        names: list[str] = [self.name, *self.synonyms]
        if self.unimod_accession:
            names.extend([f"U:{self.unimod_accession}", f"UNIMOD:{self.unimod_accession}"])
        if self.psi_mod_accession:
            names.extend([self.psi_mod_accession])
        if self.resid_accession:
            names.extend([f"R:{self.resid_accession}", f"RESID:{self.resid_accession}"])
        return list(set(names))

    def canonicalize_smiles(self):
        """Canonicalize the SMILES representation of the residue."""
        self.smiles = Chem.MolToSmiles(
            Chem.MolFromSmiles(self.smiles), canonical=True, isomericSmiles=False
        )

    def resolve_modification_accessions(self):
        """Find missing modification accession numbers from databases and verify by composition."""
        if not self.unimod_accession:
            self.resolve_unimod_accession()
        if not self.psi_mod_accession:
            self.resolve_psi_mod_accession()
        # if not self.resid_accession:
        #     self.resolve_resid_accession()

    def resolve_unimod_accession(self):
        """
        Find the Unimod accession number and verify by composition.

        Searches Unimod database by name and synonyms, validates match by composition.
        Updates the `unimod_accession` attribute if a match is found.

        Examples
        --------
        >>> residue = Residue(name="Phospho", residue="S", anchor="side-chain",
        ...                   smiles="*NC(COP(O)(O)=O)C(*)=O", ...)
        >>> residue.resolve_unimod_accession()
        >>> residue.unimod_accession
        '21'
        """
        self.unimod_accession = resolve_unimod_accession(
            names=[self.name] + (self.synonyms or []),
            delta_composition=self.delta_composition,
        )

    def resolve_psi_mod_accession(self):
        """Find the PSI-MOD accession number for the modification and verify by composition."""
        self.psi_mod_accession = resolve_psi_mod_accession(
            names=[self.name] + (self.synonyms or []),
            delta_composition=self.delta_composition,
        )

    def resolve_resid_accession(self):
        """Find the RESID accession number and verify by composition."""
        raise NotImplementedError

    def validate_accession_compositions(self) -> bool:
        """
        Validate that the composition matches the database entries.

        If the residue has a Unimod or PSI-MOD accession, verify that the composition derived from
        the SMILES string matches the composition listed in the respective database entry.

        Returns
        -------
        bool
            True if all accession compositions match, False otherwise
        """
        matches_unimod: bool
        matches_psi_mod: bool

        if self.unimod_accession is None:
            matches_unimod = True
        else:
            matches_unimod = (
                isinstance(self.unimod_entry, dict)
                and self.unimod_entry["composition"] == self.delta_composition
            )

        if self.psi_mod_accession is None:
            matches_psi_mod = True
        else:
            try:
                matches_psi_mod = (
                    isinstance(self.psi_mod_entry, dict)
                    and self.psi_mod_entry["composition"] == self.delta_composition
                )
            except (KeyError, proforma.ModificationMassNotFoundError):
                matches_psi_mod = False

        return all([matches_unimod, matches_psi_mod])
