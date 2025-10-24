import logging
import re
from pathlib import Path

from pydantic import ValidationError

from residuum import Residue, ResidueList
from residuum.sources import psimod, resid, unimod

resid_to_psimod_file = "dbs/resid/resid-to-psimod.tsv"
resid_smiles = "dbs/resid/resid-smiles.tsv"
psi_mod_file = "dbs/psimod/PSI-MOD.tsv"

LOGGER = logging.getLogger(__name__)

UNIMOD_PATTERN = re.compile(r"Unimod:(\d+)")
ANCHOR_MAP = {
    "N-term": "N-term",
    "C-term": "C-term",
    "none": "side-chain",
    "": "side-chain",
    None: "side-chain",
}
PSIMOD_PATTERN = re.compile(r"PSI-")


def _build_modification(
    resid_to_psimod_entry: dict,
    resid_entry: dict,
    psi_mod_entry: dict,
    unimod_entry: dict | None,
    smiles: str,
    residue: str,
) -> Residue | None:
    # Try to get Unimod accession from PSI-MOD entry or from RESID mapping in Unimod
    try:
        unimod_accession_from_psimod = UNIMOD_PATTERN.match(psi_mod_entry["unimod"]).group(1)
    except (AttributeError, TypeError):
        unimod_accession_from_psimod = None
    unimod_accession = unimod_accession_from_psimod or unimod_entry["id"] if unimod_entry else None
    if unimod_accession_from_psimod and unimod_entry:
        if unimod_accession != unimod_accession_from_psimod:
            LOGGER.warning(
                f"Unimod accession mismatch: {unimod_accession} (Unimod RESID match) != "
                f"{unimod_accession_from_psimod} (PSI-MOD). "
                "Keeping Unimod accession from PSI-MOD entry."
            )

    synonyms = list(set(psi_mod_entry["synonyms"] + resid_entry["Alternate Names"].split("; ")))
    if unimod_entry:
        synonyms.extend(
            [
                unimod_entry["title"],
                unimod_entry["full_name"],
                f"U:{unimod_entry['title']}",
                f"U:{unimod_entry['full_name']}",
                f"UNIMOD:{unimod_entry['title']}",
                f"UNIMOD:{unimod_entry['full_name']}",
            ]
        )

    try:
        return Residue(
            name=psi_mod_entry["name"],
            residue=residue,
            anchor=ANCHOR_MAP[psi_mod_entry["termspec"]],
            smiles=smiles or "",
            psi_mod_accession=psi_mod_entry["id"],
            unimod_accession=unimod_accession,
            resid_accession=resid_to_psimod_entry["resid-accession"],
            chebi_accession=psi_mod_entry["chebi"],
            synonyms=synonyms,
        )
    except ValidationError as e:
        LOGGER.error(f"Error building residue: {e}")


def combine_sources(
    resid_xml_file: Path | str,
    resid_smiles_file: Path | str,
    psi_mod_file: Path | str,
    unimod_file: Path | str,
) -> ResidueList:
    """
    Build ResidueList from RESID, RESID SMILES, and PSI-MOD files.

    Parameters
    ----------
    resid_xml_file
        Path to the RESID XML file
    resid_smiles
        Path to the RESID ``models.zip`` or Openbabel-generated SMILES txt file
    psi_mod_file
        Path to the PSI-MOD OBO file
    unimod_file
        Path to the Unimod XML file

    """
    resid_entries = {entry["Entry ID"]: entry for entry in resid.iterate_resid_xml(resid_xml_file)}
    resid_to_psimod = resid.get_resid_psimod_mapping(resid_xml_file)
    if Path(resid_smiles_file).suffix == ".zip":
        resid_smiles = resid.smiles_from_pdb_zip(resid_smiles_file)
    elif Path(resid_smiles_file).suffix == ".txt":
        resid_smiles = resid.smiles_from_openbabel_conversion(resid_smiles_file)
    else:
        raise ValueError(f"Unsupported file format: {resid_smiles_file}")
    psi_mod_entries = {entry["id"]: entry for entry in psimod.parse_obo(psi_mod_file)}
    unimod_entries = {
        resid_accession: entry
        for entry in unimod.parse_unimod_xml(unimod_file)
        for resid_accession in entry["resid_accessions"]
    }

    residues = []
    for resid_to_psimod_entry in resid_to_psimod:
        resid_accession = resid_to_psimod_entry["resid-accession"]
        psi_mod_accession = PSIMOD_PATTERN.sub("", resid_to_psimod_entry["psi-mod"])
        smiles = resid_smiles.get(resid_accession, None)
        resid_entry = resid_entries[resid_accession]
        if not psi_mod_accession:
            continue  # TODO: Consider keeping residue with missing PSI-MOD entry?
        psi_mod_entry = psi_mod_entries[PSIMOD_PATTERN.sub("", resid_to_psimod_entry["psi-mod"])]
        unimod_entry = unimod_entries.get(resid_accession, None)

        # PSI-MOD entry may have multiple residues (mostly for cross-links)
        for residue in psi_mod_entry["origin"].split(", "):
            res = _build_modification(
                resid_to_psimod_entry,
                resid_entry,
                psi_mod_entry,
                unimod_entry,
                smiles,
                residue,
            )
            if res:
                residues.append(res)

    return ResidueList(residues)
