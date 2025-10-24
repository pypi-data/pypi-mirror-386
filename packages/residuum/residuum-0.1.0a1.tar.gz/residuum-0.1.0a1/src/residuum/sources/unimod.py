"""Functionality to interact with the Unimod database."""

from pathlib import Path
from typing import Any
from urllib.request import urlretrieve

URL = "http://www.unimod.org/xml/unimod.xml"


def download(
    url: str | None = None,
    output_path: Path | str | None = None,
    force: bool = False,
):
    """Download the Unimod XML file from the Unimod website."""
    url = url or URL
    output_path = Path(output_path or "./dbs/unimod/unimod.xml")

    if not force and output_path.exists():
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    urlretrieve(url, output_path)


def parse_unimod_xml(unimod_xml_file: Path | str | None = None) -> list[dict[str, Any]]:
    """Convert the Unimod XML file to a dictionary."""
    unimod_xml_file = Path(unimod_xml_file or "./dbs/unimod/unimod.xml")
    download(output_path=unimod_xml_file, force=False)

    from xml.etree import ElementTree as ET

    tree = ET.parse(unimod_xml_file)
    root = tree.getroot()

    namespace = {"umod": "http://www.unimod.org/xmlns/schema/unimod_2"}
    modifications_section = root.find("umod:modifications", namespace)

    mods = []
    for mod in modifications_section.findall("umod:mod", namespace):
        mod_dict = {}

        mod_dict["id"] = mod.get("record_id")
        mod_dict["title"] = mod.get("title")
        mod_dict["full_name"] = mod.get("full_name")

        specificity_list = []
        for spec in mod.findall("umod:specificity", namespace):
            specificity = {"residue": spec.get("site"), "anchor": spec.get("position")}
            specificity_list.append(specificity)
        mod_dict["specificity"] = specificity_list

        delta = mod.find("umod:delta", namespace)
        if delta is not None:
            composition = {}
            for element in delta.findall("umod:element", namespace):
                symbol = element.get("symbol")
                number = int(element.get("number"))
                composition[symbol] = number
            mod_dict["delta_composition"] = composition
        else:
            mod_dict["delta_composition"] = {}

        resid_accessions = []
        for xref in mod.findall("umod:xref", namespace):
            if xref.find("umod:source", namespace).text == "RESID":
                resid_accessions.append(xref.find("umod:text", namespace).text)

        mod_dict["resid_accessions"] = resid_accessions

        mods.append(mod_dict)

    return mods
