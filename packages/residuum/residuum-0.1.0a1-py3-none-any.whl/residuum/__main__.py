"""Command-line interface for residuum."""

import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.logging import RichHandler

from residuum import ResidueList
from residuum.build.from_sources import combine_sources
from residuum.html import render
from residuum.sources import psimod, resid, unimod

CLI = typer.Typer()
LOGGER = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)


@CLI.command()
def validate(filepath: Annotated[Path, typer.Argument()]):
    """
    Validate residues in a file.

    Parameters
    ----------
    filepath
        Path to the residues file
    """
    LOGGER.info(f"Validating residues in {filepath}...")
    residues = ResidueList.from_file(filepath)
    not_valid = []
    for residue in residues:
        if not residue.smiles_is_amino_acid():
            LOGGER.error(
                f"> SMILES is not an amino acid: {residue.name} ({residue.residue}, {residue.anchor})"
            )
            not_valid.append(residue)
        if not residue.smiles_contains_residue():
            LOGGER.warning(
                f"> Residue not in SMILES: {residue.name} ({residue.residue}, {residue.anchor})"
            )
        if not residue.smiles_matches_accession_masses():
            LOGGER.error(f"> Mass mismatch: {residue.name} ({residue.residue}, {residue.anchor})")
            not_valid.append(residue)
    if not not_valid:
        LOGGER.info("All residues are valid.")
    else:
        invalid_residues = "\n".join(
            [f"- {residue.name} ({residue.residue}, {residue.anchor})" for residue in not_valid]
        )
        LOGGER.error(f"\nThe following residues are not valid: \n\n{invalid_residues}")
        typer.Exit(code=1)


@CLI.command()
def resolve_accessions(filepath: Annotated[Path, typer.Argument()]):
    """
    Resolve accessions for residues based on name and validated by composition.

    Parameters
    ----------
    filepath
        Path to the residues file
    """
    LOGGER.info(f"Resolving accessions in {filepath}...")
    residues = ResidueList.from_file(filepath)
    for residue in residues:
        residue.resolve_unimod_accession()
        residue.resolve_psi_mod_accession()
        # residue.resolve_resid_accession()
    residues.to_file(filepath)
    LOGGER.info("Accessions resolved.")


@CLI.command()
def build_from_databases(
    output_file: Annotated[Path, typer.Argument()],
):
    """
    Build residues from RESID, RESID SMILES, and PSI-MOD files.

    Parameters
    ----------
    output_file
        Path to the output residues file
    """
    LOGGER.info("Downloading RESID, PSI-MOD, and UNIMOD files...")

    psimod.download("./dbs/psimod/PSI-MOD.obo")
    resid.download("./dbs/resid/")
    unimod.download("./dbs/unimod/unimod.xml")

    LOGGER.info("Building residues from RESID and PSI-MOD...")

    combine_sources(
        "./dbs/resid/RESIDUES.XML",
        # "./dbs/resid/models.zip",
        "./dbs/resid/smiles.txt",  # TODO: Implement pdb_to_smiles (requires Python 3.7...)
        "./dbs/psimod/PSI-MOD.obo",
        "./dbs/unimod/unimod.xml",
    ).to_file(output_file)

    LOGGER.info("Residues built.")


@CLI.command()
def render_html(filepath: Annotated[Path, typer.Argument()]):
    """
    Render an HTML table with residues.

    Parameters
    ----------
    filepath
        Path to the residues file
    """
    LOGGER.info(f"Rendering HTML for {filepath}...")
    residues = ResidueList.from_file(filepath)
    render.render_html(residues, filepath.with_suffix(".html").as_posix())

    LOGGER.info("HTML rendered.")


def main():
    CLI()


if __name__ == "__main__":
    main()
