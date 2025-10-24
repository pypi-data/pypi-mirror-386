import base64
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import rdMolDraw2D  # type: ignore

from residuum import ResidueList
from residuum.sources import psimod

# Constants
PSI_MOD_PATH = Path("dbs/psimod/PSI-MOD.obo")

# Define URLs for the accessions
ACCESSION_URLS = {
    "psi_mod": "http://www.ebi.ac.uk/ontology-lookup/?termId={}",
    "unimod": "https://unimod.org/modifications_view.php?editid1={}",
    "chebi": "https://www.ebi.ac.uk/chebi/searchId.do?chebiId={}",
    "resid": "https://proteininformationresource.org/cgi-bin/resid_entry_xml.pl?id={}",
}
ACCESSION_COLORS = {
    "psi_mod": "primary",
    "unimod": "secondary",
    "chebi": "success",
    "resid": "info",
}


def _smiles_to_img(smiles: str, size: int = 100) -> str | None:
    """Convert SMILES to an image and return it as a base64-encoded string."""
    mol = Chem.MolFromSmiles(smiles)

    if not mol:
        return None

    AllChem.Compute2DCoords(mol)  # type: ignore
    drawer = rdMolDraw2D.MolDraw2DCairo(size, size)
    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    img_bytes = drawer.GetDrawingText()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    return f'<img src="data:image/png;base64,{img_b64}" alt="{smiles}" class="img" />'


def render_html(modifications: ResidueList, output_html: str) -> None:
    """
    Generates an HTML file with a table for each modification and a modal for detailed view.

    Parameters
    ----------
    modifications : ResidueList
        List of Residue objects.
    output_html : str
        Path to the output HTML file.
    """
    # Convert modifications to a list of dictionaries with processed fields

    psimod_descriptions = {
        entry["id"]: entry["definition"] for entry in psimod.parse_obo(PSI_MOD_PATH)
    }

    rows = []
    for mod in modifications:
        row = mod.model_dump()
        row["smiles_img"] = _smiles_to_img(mod.smiles) if mod.smiles else ""
        row["smiles_img_large"] = _smiles_to_img(mod.smiles, size=400) if mod.smiles else ""
        row["accessions"] = {key: None for key in ["psi_mod", "unimod", "resid", "chebi"]}
        row["accession_urls"] = {key: None for key in ["psi_mod", "unimod", "resid", "chebi"]}
        if mod.psi_mod_accession:
            row["accessions"]["psi_mod"] = mod.psi_mod_accession
            row["accession_urls"]["psi_mod"] = ACCESSION_URLS["psi_mod"].format(
                mod.psi_mod_accession
            )
        if mod.unimod_accession:
            row["accessions"]["unimod"] = mod.unimod_accession
            row["accession_urls"]["unimod"] = ACCESSION_URLS["unimod"].format(mod.unimod_accession)
        if mod.chebi_accession:
            row["accessions"]["chebi"] = mod.chebi_accession
            row["accession_urls"]["chebi"] = ACCESSION_URLS["chebi"].format(mod.chebi_accession)
        if mod.resid_accession:
            row["accessions"]["resid"] = mod.resid_accession
            row["accession_urls"]["resid"] = ACCESSION_URLS["resid"].format(mod.resid_accession)
        row["synonyms"] = mod.synonyms or []
        row["description"] = psimod_descriptions.get(mod.psi_mod_accession, "")

        rows.append(row)

    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("src/residuum/html/templates/modlist.html")

    # Render the template with the data
    html_content = template.render(rows=rows, accession_colors=ACCESSION_COLORS)

    # Write the HTML content to the output file
    with open(output_html, "w", encoding="utf-8") as file:
        file.write(html_content)
