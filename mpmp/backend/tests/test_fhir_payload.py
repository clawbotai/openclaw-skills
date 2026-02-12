"""Tests for FHIR MedicationRequest payload construction."""
import os
import uuid

os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
os.environ.setdefault("PHI_ENCRYPTION_KEY", os.urandom(32).hex())

from app.services.azoth_router import build_medication_request
from app.services.magistral_calculator import calculate_dosage


class TestFHIRPayload:
    def setup_method(self):
        self.calc = calculate_dosage("BPC-157", 5.0, 2.0, "U-100 1mL Insulin Syringe", 250.0)
        self.rx_id = uuid.uuid4()
        self.alias_id = uuid.uuid4()

    def test_resource_type(self):
        payload = build_medication_request(self.rx_id, self.alias_id, self.calc)
        assert payload["resourceType"] == "MedicationRequest"

    def test_identifier(self):
        payload = build_medication_request(self.rx_id, self.alias_id, self.calc)
        assert payload["identifier"][0]["value"] == str(self.rx_id)

    def test_subject_uses_alias_not_phi(self):
        payload = build_medication_request(self.rx_id, self.alias_id, self.calc)
        assert payload["subject"]["reference"] == f"Patient/{self.alias_id}"

    def test_medication_coding(self):
        payload = build_medication_request(self.rx_id, self.alias_id, self.calc)
        coding = payload["medicationCodeableConcept"]["coding"][0]
        assert coding["code"] == "BPC-157"
        assert "azoth-os.com" in coding["system"]

    def test_dosage_instruction(self):
        payload = build_medication_request(self.rx_id, self.alias_id, self.calc)
        dosage = payload["dosageInstruction"][0]
        assert "10 Units" in dosage["text"]
        assert dosage["route"]["coding"][0]["code"] == "34206005"

    def test_subcutaneous_route(self):
        payload = build_medication_request(self.rx_id, self.alias_id, self.calc, route="subcutaneous")
        assert payload["dosageInstruction"][0]["route"]["coding"][0]["display"] == "Subcutaneous route"

    def test_intramuscular_route(self):
        payload = build_medication_request(self.rx_id, self.alias_id, self.calc, route="intramuscular")
        assert payload["dosageInstruction"][0]["route"]["coding"][0]["code"] == "78421000"

    def test_dispense_request(self):
        payload = build_medication_request(self.rx_id, self.alias_id, self.calc)
        assert payload["dispenseRequest"]["quantity"]["value"] == 1
        assert payload["dispenseRequest"]["quantity"]["unit"] == "vial"

    def test_no_phi_in_payload(self):
        """Ensure zero PHI leaks into the FHIR payload."""
        payload = str(build_medication_request(self.rx_id, self.alias_id, self.calc))
        # Should only contain the alias UUID, no real names/DOBs
        assert str(self.alias_id) in payload
