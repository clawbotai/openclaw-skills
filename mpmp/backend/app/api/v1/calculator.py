"""Magistral Dosage Calculator endpoints."""
from fastapi import APIRouter, Depends, HTTPException

from app.middleware.rbac import require_roles
from app.models.user import User, UserRole
from app.schemas.calculator import CalculateRequest, CalculateResponse, PresetResponse
from app.services.magistral_calculator import calculate_dosage, PEPTIDE_PRESETS

router = APIRouter(prefix="/calculator", tags=["calculator"])


@router.post("/calculate", response_model=CalculateResponse)
async def calculate(
    body: CalculateRequest,
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN, UserRole.PROVIDER)),
):
    """Compute dosage from prescription parameters."""
    try:
        result = calculate_dosage(
            compound=body.compound,
            vial_size_mg=body.vial_size_mg,
            diluent_ml=body.diluent_ml,
            syringe_type=body.syringe_type,
            target_dose_mcg=body.target_dose_mcg,
            route=body.route,
            frequency=body.frequency,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return CalculateResponse(
        compound=result.compound,
        vial_size_mg=result.vial_size_mg,
        diluent_ml=result.diluent_ml,
        syringe_type=result.syringe_type,
        target_dose_mcg=result.target_dose_mcg,
        total_mass_mcg=result.total_mass_mcg,
        concentration_mcg_per_ml=result.concentration_mcg_per_ml,
        draw_volume_ml=result.draw_volume_ml,
        syringe_units=result.syringe_units,
        doses_per_vial=result.doses_per_vial,
        human_readable=result.human_readable,
        fhir_dosage_text=result.fhir_dosage_text,
    )


@router.get("/presets", response_model=list[PresetResponse])
async def get_presets(
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN, UserRole.PROVIDER)),
):
    """List common peptide presets."""
    return [
        PresetResponse(name=name, **data)
        for name, data in PEPTIDE_PRESETS.items()
    ]
