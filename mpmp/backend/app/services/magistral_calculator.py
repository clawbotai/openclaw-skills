"""Magistral Dosage Calculator — deterministic peptide reconstitution math.

Bridges mass-based prescriptions (mg/mcg) to volume-based patient instructions (mL/Units).
Generates FHIR DosageInstruction text and patient-friendly instructions.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class DosageCalculation:
    compound: str
    vial_size_mg: float
    diluent_ml: float
    syringe_type: str  # e.g., "U-100 1mL Insulin Syringe"
    target_dose_mcg: float

    # Computed
    total_mass_mcg: float = 0.0
    concentration_mcg_per_ml: float = 0.0
    draw_volume_ml: float = 0.0
    syringe_units: float = 0.0
    doses_per_vial: int = 0
    human_readable: str = ""
    fhir_dosage_text: str = ""


def _syringe_multiplier(syringe_type: str) -> int:
    """Return units-per-mL for a given syringe type."""
    syringe_type_lower = syringe_type.lower()
    if "u-100" in syringe_type_lower:
        return 100
    elif "u-50" in syringe_type_lower:
        return 50
    elif "u-40" in syringe_type_lower:
        return 40
    return 100  # Default U-100


def _route_display(route: str) -> str:
    routes = {
        "subcutaneous": "subcutaneously",
        "intramuscular": "intramuscularly",
        "intravenous": "intravenously",
        "intradermal": "intradermally",
        "oral": "orally",
    }
    return routes.get(route.lower(), route)


def calculate_dosage(
    compound: str,
    vial_size_mg: float,
    diluent_ml: float,
    syringe_type: str,
    target_dose_mcg: float,
    route: str = "subcutaneous",
    frequency: str = "daily",
) -> DosageCalculation:
    """Pure deterministic calculation — no side effects, no DB calls.

    Args:
        compound: Peptide/compound name (e.g., "BPC-157")
        vial_size_mg: Total mass in vial in milligrams (e.g., 5.0)
        diluent_ml: Volume of bacteriostatic water in mL (e.g., 2.0)
        syringe_type: Syringe specification (e.g., "U-100 1mL Insulin Syringe")
        target_dose_mcg: Prescribed dose in micrograms (e.g., 250.0)
        route: Administration route (default: subcutaneous)
        frequency: Dosing frequency (default: daily)

    Returns:
        DosageCalculation with all computed fields populated
    """
    if vial_size_mg <= 0:
        raise ValueError("Vial size must be positive")
    if diluent_ml <= 0:
        raise ValueError("Diluent volume must be positive")
    if target_dose_mcg <= 0:
        raise ValueError("Target dose must be positive")

    # Core math
    total_mass_mcg = vial_size_mg * 1000.0
    concentration = total_mass_mcg / diluent_ml
    draw_volume = target_dose_mcg / concentration
    multiplier = _syringe_multiplier(syringe_type)
    units = draw_volume * multiplier
    doses = int(total_mass_mcg / target_dose_mcg)

    # Round to practical precision
    draw_volume = round(draw_volume, 4)
    units = round(units, 1)

    # Human-readable instruction
    route_str = _route_display(route)
    human = (
        f"Reconstitute {compound} {vial_size_mg}mg vial with {diluent_ml}mL BAC Water. "
        f"Draw {units:.0f} Units ({draw_volume:.2f}mL) and inject {route_str} {frequency}."
    )

    # FHIR-compatible text
    fhir_text = (
        f"Reconstitute with {diluent_ml}mL Bacteriostatic Water. "
        f"Draw {units:.0f} Units and inject {route_str} {frequency}."
    )

    return DosageCalculation(
        compound=compound,
        vial_size_mg=vial_size_mg,
        diluent_ml=diluent_ml,
        syringe_type=syringe_type,
        target_dose_mcg=target_dose_mcg,
        total_mass_mcg=total_mass_mcg,
        concentration_mcg_per_ml=concentration,
        draw_volume_ml=draw_volume,
        syringe_units=units,
        doses_per_vial=doses,
        human_readable=human,
        fhir_dosage_text=fhir_text,
    )


# Common peptide presets for quick reference
PEPTIDE_PRESETS = {
    "BPC-157": {"typical_dose_mcg": 250, "typical_vial_mg": 5.0, "route": "subcutaneous"},
    "TB-500": {"typical_dose_mcg": 2500, "typical_vial_mg": 5.0, "route": "subcutaneous"},
    "Semaglutide": {"typical_dose_mcg": 250, "typical_vial_mg": 5.0, "route": "subcutaneous"},
    "Tirzepatide": {"typical_dose_mcg": 2500, "typical_vial_mg": 10.0, "route": "subcutaneous"},
    "CJC-1295/Ipamorelin": {"typical_dose_mcg": 300, "typical_vial_mg": 5.0, "route": "subcutaneous"},
    "PT-141": {"typical_dose_mcg": 1750, "typical_vial_mg": 10.0, "route": "subcutaneous"},
    "Sermorelin": {"typical_dose_mcg": 200, "typical_vial_mg": 9.0, "route": "subcutaneous"},
    "NAD+": {"typical_dose_mcg": 100000, "typical_vial_mg": 500.0, "route": "subcutaneous"},
}
