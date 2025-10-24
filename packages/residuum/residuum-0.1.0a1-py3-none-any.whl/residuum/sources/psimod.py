"""Functionality to interact with PSI-MOD controlled vocabulary."""

import re
from pathlib import Path
from typing import Any
from urllib.request import urlretrieve

from pyteomics.mass import Composition

URL = "https://raw.githubusercontent.com/HUPO-PSI/psi-mod/master/PSI-MOD.obo"

ATOM_PATTERN = re.compile(r"(?:\((?P<isotope>\d+)\))?(?P<atom>[a-zA-Z]+)")


def download(output_path: Path | str, url: str | None = None, force=False):
    """Download the PSI-MOD OBO file from the PSI-MOD website."""
    url = url or URL
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not force and output_path.exists():
        return

    urlretrieve(url, output_path)


def parse_obo(input_obo: Path | str) -> list[dict[str, Any]]:
    """
    Read and parse specific fields from PSI-MOD OBO file.

    Parameters
    ----------
    input_obo
        Path to the input OBO file.

    """
    terms = []
    current_term: dict[str, Any] = {}

    chebi_pattern = re.compile(r"[ \[]ChEBI:(\d+)[,\]]")

    with open(input_obo, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line == "[Term]":
                if current_term:
                    terms.append(current_term)
                current_term = {
                    "id": "",
                    "name": "",
                    "definition": "",
                    "synonyms": [],
                    "diff-formula": Composition(),
                    "formula": Composition(),
                    "origin": "",
                    "source": "",
                    "termspec": "",
                    "unimod": "",
                    "uniprot": "",
                }
            elif line.startswith("id: "):
                current_term["id"] = line.split(": ", 1)[1]
            elif line.startswith("name: "):
                current_term["name"] = line.split(": ", 1)[1]
            elif line.startswith("def: "):
                chebi_match = chebi_pattern.search(line)
                current_term["chebi"] = chebi_match.group(1) if chebi_match else ""
                current_term["definition"] = line.split('"')[1]
            elif line.startswith("synonym: "):
                synonym = line.split('"')[1]
                current_term["synonyms"].append(synonym)
            elif line.startswith("xref: DiffFormula: "):
                formula_str = line.split('"')[1]
                current_term["diff-formula"] = (
                    None if formula_str == "none" else _parse_composition(formula_str)
                )
            elif line.startswith("xref: Formula: "):
                formula_str = line.split('"')[1]
                current_term["formula"] = (
                    None if formula_str == "none" else _parse_composition(formula_str)
                )
            elif line.startswith("xref: Origin: "):
                current_term["origin"] = line.split('"')[1]
            elif line.startswith("xref: Source: "):
                current_term["source"] = line.split('"')[1]
            elif line.startswith("xref: TermSpec: "):
                current_term["termspec"] = line.split('"')[1]
            elif line.startswith("xref: Unimod: "):
                current_term["unimod"] = line.split('"')[1]
            elif line.startswith("xref: uniprot.ptm:"):
                current_term["uniprot"] = line.split(":")[1]
            elif line.startswith("is_obsolete: true"):
                current_term: dict[str, Any] = {}

    if current_term:
        terms.append(current_term)

    return terms


def _parse_composition(composition: str) -> Composition:
    """Parse the composition string from the PSI-MOD OBO file."""
    composition_list = composition.split(" ")
    composition_dict = {}
    for i in range(0, len(composition_list), 2):
        atom_str = composition_list[i]
        count_str = composition_list[i + 1]
        isotope, atom_str = ATOM_PATTERN.match(atom_str).groups()
        atom_str = f"{atom_str}[{isotope}]" if isotope else atom_str
        count_str = int(count_str) if count_str else 1
        composition_dict[atom_str] = count_str
    return Composition(composition_dict)
