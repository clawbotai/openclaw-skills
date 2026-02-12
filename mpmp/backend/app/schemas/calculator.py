"""Magistral calculator schemas."""
from typing import Optional
from pydantic import BaseModel, Field


class CalculateRequest(BaseModel):
    compound: str = Field(..., description="Peptide/compound name")
    vial_size_mg: float = Field(..., gt=0, description="Vial size in milligrams")
    diluent_ml: float = Field(..., gt=0, description="Bacteriostatic water volume in mL")
    syringe_type: str = Field(default="U-100 1mL Insulin Syringe")
    target_dose_mcg: float = Field(..., gt=0, description="Target dose in micrograms")
    route: str = Field(default="subcutaneous")
    frequency: str = Field(default="daily")


class CalculateResponse(BaseModel):
    compound: str
    vial_size_mg: float
    diluent_ml: float
    syringe_type: str
    target_dose_mcg: float
    total_mass_mcg: float
    concentration_mcg_per_ml: float
    draw_volume_ml: float
    syringe_units: float
    doses_per_vial: int
    human_readable: str
    fhir_dosage_text: str


class PresetResponse(BaseModel):
    name: str
    typical_dose_mcg: float
    typical_vial_mg: float
    route: str
