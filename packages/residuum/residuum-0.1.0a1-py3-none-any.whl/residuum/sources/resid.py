"""Functionality to interact with RESID."""

import logging
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Generator
from ftplib import FTP
from os import PathLike
from pathlib import Path
from typing import Any

from rdkit import Chem

LOGGER = logging.getLogger(__name__)

URL = "ftp.proteininformationresource.org"
PATH = "/pir_databases/other_databases/resid"
USER = "anonymous"
PASSWORD = "pw"


def download(output_dir: Path | str, url: str | None = None, force=False):
    """Download the RESID XML and models.zip files from the RESID FTP server."""
    url = url or URL
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if not force and all(
        (output_dir / filename).exists() for filename in ["RESIDUES.XML", "models.zip"]
    ):
        return

    with FTP(url) as ftp:
        ftp.login(USER, PASSWORD)

        for filename in ["RESIDUES.XML", "models.zip"]:
            with open(output_dir / filename, "wb") as f:
                ftp.retrbinary("RETR " + PATH + "/" + filename, f.write)


def iterate_resid_xml(xml_file: str | PathLike) -> Generator[dict[str, Any], None, None]:
    """
    Iterate over each Entry in the RESID XML file and yield a dictionary of its data.

    Parameters
    ----------
    xml_file
        Path to the input XML file.
    """
    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Loop through each Entry in the XML
    for entry in root.findall("Entry"):
        row = {}
        row["Entry ID"] = entry.attrib.get("id", "")

        header_element = entry.find("Header")
        row["Code"] = header_element.findtext("Code", "")

        dates = header_element.find("Dates")
        row["Creation Date"] = dates.findtext("CreationDate", "")
        row["Structure Revision Date"] = dates.findtext("StrucRevDate", "")
        row["Text Change Date"] = dates.findtext("TextChngDate", "")

        names = entry.find("Names")
        row["Name"] = names.findtext("Name", "")
        alternate_names = [alt_name.text for alt_name in names.findall("AlternateName")]
        row["Alternate Names"] = "; ".join(alternate_names)
        row["Systematic Name"] = names.findtext("SystematicName", "")
        xrefs = [xref.text for xref in names.findall("Xref")]
        row["Xrefs"] = "; ".join(xrefs)

        formula_block = entry.find("FormulaBlock")
        row["Chemical Formula"] = formula_block.findtext("Formula", "")
        row["Chemical Weight"] = (
            formula_block.find("Weight[@type='chemical']").text
            if formula_block.find("Weight[@type='chemical']") is not None
            else ""
        )
        row["Physical Weight"] = (
            formula_block.find("Weight[@type='physical']").text
            if formula_block.find("Weight[@type='physical']") is not None
            else ""
        )

        correction_blocks = entry.findall("CorrectionBlock")
        if correction_blocks:
            correction_uids = []
            correction_labels = []
            correction_formulas = []
            correction_chemical_weights = []
            correction_physical_weights = []
            for cb in correction_blocks:
                correction_uids.append(cb.attrib.get("uids", ""))
                correction_labels.append(cb.attrib.get("label", ""))
                correction_formulas.append(cb.findtext("Formula", ""))
                correction_chemical_weights.append(
                    cb.find("Weight[@type='chemical']").text
                    if cb.find("Weight[@type='chemical']") is not None
                    else ""
                )
                correction_physical_weights.append(
                    cb.find("Weight[@type='physical']").text
                    if cb.find("Weight[@type='physical']") is not None
                    else ""
                )
            row["Correction Block (uids)"] = "; ".join(correction_uids)
            row["Correction Block (label)"] = "; ".join(correction_labels)
            row["Correction Chemical Formula"] = "; ".join(correction_formulas)
            row["Correction Chemical Weight"] = "; ".join(correction_chemical_weights)
            row["Correction Physical Weight"] = "; ".join(correction_physical_weights)
        else:
            row["Correction Block (uids)"] = ""
            row["Correction Block (label)"] = ""
            row["Correction Chemical Formula"] = ""
            row["Correction Chemical Weight"] = ""
            row["Correction Physical Weight"] = ""

        references = entry.findall("ReferenceBlock")
        authors: list[str] = []
        citations: list[str] = []
        titles: list[str] = []
        dois: list[str] = []
        pmids: list[str] = []
        notes: list[str] = []
        for ref in references:
            authors.extend(
                [
                    author.text
                    for author in ref.find("Authors").findall("Author")
                    if author.text is not None
                ]
            )
            group = ref.find("Authors").findtext("Group", "")
            if group:
                authors.append(group)
            citations.append(ref.findtext("Citation", ""))
            titles.append(ref.findtext("Title", ""))
            dois.extend([xref.text for xref in ref.findall("Xref") if xref.text.startswith("DOI")])
            pmids.extend(
                [xref.text for xref in ref.findall("Xref") if xref.text.startswith("PMID")]
            )
            notes.append(ref.findtext("Note", ""))
        row["Authors"] = "; ".join(authors)
        row["Citation"] = "; ".join(citations)
        row["Title"] = "; ".join(titles)
        row["DOIs"] = "; ".join(dois)
        row["PMIDs"] = "; ".join(pmids)
        row["Notes"] = "; ".join(notes)

        row["Comment"] = entry.findtext("Comment", "")

        sequence_codes = entry.findall("SequenceCode")
        sequence_specs: list[str] = []
        abbreviations: list[str] = []
        sequence_xrefs: list[str] = []
        for sc in sequence_codes:
            sequence_specs.append(sc.findtext("SequenceSpec", ""))
            abbreviations.append(sc.findtext("Abbreviation", ""))
            sequence_xrefs.append(sc.findtext("Xref", ""))
        row["Sequence Spec"] = "; ".join(sequence_specs)
        row["Abbreviation"] = "; ".join(abbreviations)
        row["Sequence Xrefs"] = "; ".join(sequence_xrefs)

        row["Source"] = entry.findtext("Source", "")

        features = entry.find("Features")
        if features:
            feature_types: list[str] = []
            feature_links: list[str] = []
            feature_keys: list[str] = []
            feature_notes: list[str] = []
            for feature in features.findall("Feature"):
                feature_types.append(feature.attrib.get("type", ""))
                feature_links.append(feature.attrib.get("link", ""))
                feature_keys.append(feature.attrib.get("key", ""))
                feature_notes.append(feature.findtext("Note", ""))
            row["Feature Types"] = "; ".join(feature_types)
            row["Feature Links"] = "; ".join(feature_links)
            row["Feature Keys"] = "; ".join(feature_keys)
            row["Feature Notes"] = "; ".join(feature_notes)
        else:
            row["Feature Types"] = None
            row["Feature Links"] = None
            row["Feature Keys"] = None
            row["Feature Notes"] = None

        image_element = entry.find("Image")
        row["Image"] = image_element.attrib.get("src", "") if image_element is not None else None

        model_element = entry.find("Model")
        row["Model"] = model_element.attrib.get("src", "") if model_element is not None else None

        yield row


def smiles_from_pdb_zip(zip_file: Path | str) -> dict[str, str]:
    """
    Extract PDB models from a ZIP file and  convert them to SMILES strings for each RESID ID.

    Parameters
    ----------
    zip_file : str
        Path to the ZIP file containing PDB models.

    Returns
    -------
    Dict[str, str]
        Dictionary mapping RESID IDs to SMILES strings.
    """

    # Open the ZIP file
    with zipfile.ZipFile(zip_file, "r") as z:
        smiles_dict = {}
        for model_filename in z.namelist():
            try:
                mol = Chem.MolFromPDBBlock(z.read(model_filename).decode("utf-8"))
                smiles = Chem.MolToSmiles(mol)
            except Exception as e:
                LOGGER.error(f"Error converting PDB to SMILES: {e}")
                smiles = None
            smiles_dict[Path(model_filename).stem] = smiles
    return smiles_dict


def smiles_from_openbabel_conversion(smiles_file: Path | str) -> dict[str, str]:
    """
    Read smiles from a file generated by OpenBabel.

    Parameters
    ----------
    smiles_file
        Path to the input file.

    Returns
    -------
    Dict[str, str]
        Dictionary mapping RESID IDs to SMILES strings.
    """
    smiles_dict = {}
    with open(smiles_file, "r") as file:
        for line in file:
            resid_id, smiles = line.strip().split("\t")
            smiles_dict[resid_id] = smiles
    return smiles_dict


def get_resid_psimod_mapping(
    resid_xml_file: Path | str,
) -> Generator[dict[str, Any], None, None]:
    """
    Extracts data from RESID XML file and yield dictionaries with mapping data.

    Parameters
    ----------
    xml_file
        Path to the input XML file.

    Yields
    -------
    Dict[str, Any]
        List of dictionaries with keys ``resid-accession``, ``sequence-spec``, ``psi-mod``,
        and ``correction-formula``.
    """
    # Parse the XML file
    tree = ET.parse(str(resid_xml_file))
    root = tree.getroot()

    # Loop through each Entry in the XML
    for entry in root.findall("Entry"):
        resid_accession = entry.attrib.get("id", "")

        # Create a dictionary to map correction block labels to formulas
        correction_block_dict = {}
        for cb in entry.findall("CorrectionBlock"):
            label = cb.attrib.get("label", "")
            formula = cb.findtext("Formula", "")
            correction_block_dict[label] = formula

        # Process each SequenceCode block
        for seq_code in entry.findall("SequenceCode"):
            link = seq_code.attrib.get("link", "")
            sequence_spec = seq_code.findtext("SequenceSpec", "")
            psi_mod_xref = ""
            for xref in seq_code.findall("Xref"):
                if xref.text and "PSI-MOD" in xref.text:
                    psi_mod_xref = xref.text
                    break

            correction_formula = correction_block_dict.get(link, "")

            yield {
                "resid-accession": resid_accession,
                "sequence-spec": sequence_spec,
                "psi-mod": psi_mod_xref,
                "correction-formula": correction_formula,
            }
