"""External modification database integration (Unimod, PSI-MOD, RESID)."""

from typing import Any

from pyteomics import mass, proforma


def resolve_unimod_accession(names: list[str], delta_composition: mass.Composition) -> str | None:
    """Find the Unimod accession number for a modification by name and verify by composition."""
    for name in names:
        try:
            unimod_entry = proforma.UnimodResolver().resolve(name)
        except (KeyError, proforma.ModificationMassNotFoundError):
            continue
        if unimod_entry["composition"] == delta_composition:
            return str(unimod_entry["id"])
    return None


def resolve_psi_mod_accession(names: list[str], delta_composition: mass.Composition) -> str | None:
    """Find the PSI-MOD accession number for a modification by name and verify by composition."""
    for name in names:
        try:
            psi_mod_entry = proforma.PSIModResolver().resolve(name)
        except (KeyError, proforma.ModificationMassNotFoundError):
            continue
        if psi_mod_entry["composition"] == delta_composition:
            return psi_mod_entry["id"]
    return None


def get_unimod_entry(accession: int) -> dict[str, Any] | None:
    """Get Unimod entry by accession number."""
    try:
        return proforma.UnimodResolver().resolve(accession)
    except KeyError:
        return None


def get_psi_mod_entry(accession: str) -> dict[str, Any] | None:
    """Get PSI-MOD entry by accession."""
    try:
        return proforma.PSIModResolver().resolve(accession)
    except KeyError:
        return None
