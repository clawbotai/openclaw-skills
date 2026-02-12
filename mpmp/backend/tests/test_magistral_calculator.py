"""Extensive unit tests for the Magistral Dosage Calculator — pure math, zero side effects."""
import pytest
from app.services.magistral_calculator import calculate_dosage, PEPTIDE_PRESETS


class TestBasicCalculations:
    """Core reconstitution math verification."""

    def test_bpc157_standard(self):
        """BPC-157: 5mg vial, 2mL BAC water, 250mcg dose, U-100 syringe."""
        r = calculate_dosage("BPC-157", 5.0, 2.0, "U-100 1mL Insulin Syringe", 250.0)
        assert r.total_mass_mcg == 5000.0
        assert r.concentration_mcg_per_ml == 2500.0
        assert r.draw_volume_ml == 0.1
        assert r.syringe_units == 10.0
        assert r.doses_per_vial == 20

    def test_tb500_standard(self):
        """TB-500: 5mg vial, 2mL diluent, 2500mcg dose."""
        r = calculate_dosage("TB-500", 5.0, 2.0, "U-100 1mL Insulin Syringe", 2500.0)
        assert r.total_mass_mcg == 5000.0
        assert r.concentration_mcg_per_ml == 2500.0
        assert r.draw_volume_ml == 1.0
        assert r.syringe_units == 100.0
        assert r.doses_per_vial == 2

    def test_semaglutide_low_dose(self):
        """Semaglutide: 5mg vial, 3mL diluent, 250mcg dose."""
        r = calculate_dosage("Semaglutide", 5.0, 3.0, "U-100 1mL Insulin Syringe", 250.0)
        assert r.total_mass_mcg == 5000.0
        assert abs(r.concentration_mcg_per_ml - 1666.6667) < 0.1
        assert abs(r.draw_volume_ml - 0.15) < 0.001
        assert abs(r.syringe_units - 15.0) < 0.1
        assert r.doses_per_vial == 20

    def test_tirzepatide_high_dose(self):
        """Tirzepatide: 10mg vial, 2mL diluent, 2500mcg dose."""
        r = calculate_dosage("Tirzepatide", 10.0, 2.0, "U-100 1mL Insulin Syringe", 2500.0)
        assert r.total_mass_mcg == 10000.0
        assert r.concentration_mcg_per_ml == 5000.0
        assert r.draw_volume_ml == 0.5
        assert r.syringe_units == 50.0
        assert r.doses_per_vial == 4

    def test_nad_large_dose(self):
        """NAD+: 500mg vial, 10mL diluent, 100mg (100000mcg) dose."""
        r = calculate_dosage("NAD+", 500.0, 10.0, "U-100 1mL Insulin Syringe", 100000.0)
        assert r.total_mass_mcg == 500000.0
        assert r.concentration_mcg_per_ml == 50000.0
        assert r.draw_volume_ml == 2.0
        assert r.syringe_units == 200.0
        assert r.doses_per_vial == 5


class TestSyringeTypes:
    """Verify correct unit conversion for different syringe types."""

    def test_u100(self):
        r = calculate_dosage("Test", 5.0, 2.0, "U-100 1mL Insulin Syringe", 250.0)
        assert r.syringe_units == 10.0

    def test_u50(self):
        r = calculate_dosage("Test", 5.0, 2.0, "U-50 Syringe", 250.0)
        assert r.syringe_units == 5.0

    def test_u40(self):
        r = calculate_dosage("Test", 5.0, 2.0, "U-40 Syringe", 250.0)
        assert r.syringe_units == 4.0

    def test_unknown_defaults_u100(self):
        r = calculate_dosage("Test", 5.0, 2.0, "Random Syringe", 250.0)
        assert r.syringe_units == 10.0  # Default U-100


class TestEdgeCases:
    """Boundary and error conditions."""

    def test_zero_vial_size_raises(self):
        with pytest.raises(ValueError, match="Vial size must be positive"):
            calculate_dosage("Test", 0.0, 2.0, "U-100", 250.0)

    def test_negative_vial_size_raises(self):
        with pytest.raises(ValueError, match="Vial size must be positive"):
            calculate_dosage("Test", -1.0, 2.0, "U-100", 250.0)

    def test_zero_diluent_raises(self):
        with pytest.raises(ValueError, match="Diluent volume must be positive"):
            calculate_dosage("Test", 5.0, 0.0, "U-100", 250.0)

    def test_zero_dose_raises(self):
        with pytest.raises(ValueError, match="Target dose must be positive"):
            calculate_dosage("Test", 5.0, 2.0, "U-100", 0.0)

    def test_very_small_dose(self):
        """1mcg dose from a 5mg vial — extreme precision."""
        r = calculate_dosage("Test", 5.0, 2.0, "U-100 1mL Insulin Syringe", 1.0)
        assert r.concentration_mcg_per_ml == 2500.0
        assert abs(r.draw_volume_ml - 0.0004) < 0.00001
        assert r.doses_per_vial == 5000

    def test_dose_equals_vial(self):
        """Single-dose vial — entire contents in one draw."""
        r = calculate_dosage("Test", 5.0, 2.0, "U-100 1mL Insulin Syringe", 5000.0)
        assert r.draw_volume_ml == 2.0
        assert r.syringe_units == 200.0
        assert r.doses_per_vial == 1


class TestOutputStrings:
    """Verify human-readable and FHIR text generation."""

    def test_human_readable_contains_key_info(self):
        r = calculate_dosage("BPC-157", 5.0, 2.0, "U-100 1mL Insulin Syringe", 250.0)
        assert "BPC-157" in r.human_readable
        assert "5.0mg" in r.human_readable
        assert "2.0mL BAC Water" in r.human_readable
        assert "10 Units" in r.human_readable
        assert "subcutaneously" in r.human_readable
        assert "daily" in r.human_readable

    def test_fhir_text_format(self):
        r = calculate_dosage("BPC-157", 5.0, 2.0, "U-100 1mL Insulin Syringe", 250.0)
        assert "Reconstitute with 2.0mL Bacteriostatic Water" in r.fhir_dosage_text
        assert "10 Units" in r.fhir_dosage_text

    def test_intramuscular_route(self):
        r = calculate_dosage("Test", 5.0, 2.0, "U-100", 250.0, route="intramuscular")
        assert "intramuscularly" in r.human_readable

    def test_custom_frequency(self):
        r = calculate_dosage("Test", 5.0, 2.0, "U-100", 250.0, frequency="twice weekly")
        assert "twice weekly" in r.human_readable


class TestPresets:
    """Verify preset data integrity."""

    def test_all_presets_have_required_fields(self):
        for name, data in PEPTIDE_PRESETS.items():
            assert "typical_dose_mcg" in data
            assert "typical_vial_mg" in data
            assert "route" in data
            assert data["typical_dose_mcg"] > 0
            assert data["typical_vial_mg"] > 0

    def test_presets_produce_valid_calculations(self):
        for name, data in PEPTIDE_PRESETS.items():
            r = calculate_dosage(
                name, data["typical_vial_mg"], 2.0,
                "U-100 1mL Insulin Syringe", data["typical_dose_mcg"],
                route=data["route"],
            )
            assert r.draw_volume_ml > 0
            assert r.syringe_units > 0
            assert r.doses_per_vial >= 1
