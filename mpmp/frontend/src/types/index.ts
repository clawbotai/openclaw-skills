// ─── Auth ───
export interface User {
  id: string;
  email: string;
  role: "superadmin" | "provider" | "clinical_staff" | "patient";
  mfa_enabled: boolean;
  is_active: boolean;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// ─── Patient ───
export interface Patient {
  id: string;
  user_id: string;
  azoth_alias_id: string;
  first_name: string;
  last_name: string;
  dob: string;
  demographics?: string;
  weight_kg?: number;
  height_cm?: number;
  bmi?: number;
}

export interface PatientListItem {
  id: string;
  azoth_alias_id: string;
  first_name: string;
  last_name: string;
  weight_kg?: number;
}

// ─── Clinical Notes ───
export interface SOAPData {
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
}

export interface ClinicalNote {
  id: string;
  patient_id: string;
  provider_id: string;
  version: number;
  soap: SOAPData;
  signed_at?: string;
  created_at: string;
  updated_at: string;
}

// ─── Appointments ───
export type AppointmentStatus =
  | "scheduled"
  | "checked_in"
  | "in_progress"
  | "completed"
  | "cancelled"
  | "no_show";

export interface Appointment {
  id: string;
  patient_id: string;
  provider_id: string;
  start_time: string;
  duration_minutes: number;
  status: AppointmentStatus;
  telehealth_link?: string;
  notes?: string;
  created_at: string;
}

// ─── Calculator ───
export interface DosageResult {
  compound: string;
  vial_size_mg: number;
  diluent_ml: number;
  syringe_type: string;
  target_dose_mcg: number;
  total_mass_mcg: number;
  concentration_mcg_per_ml: number;
  draw_volume_ml: number;
  syringe_units: number;
  doses_per_vial: number;
  human_readable: string;
  fhir_dosage_text: string;
}

export interface PeptidePreset {
  name: string;
  typical_dose_mcg: number;
  typical_vial_mg: number;
  route: string;
}

// ─── Inventory ───
export type InventoryStatus = "in_stock" | "low_stock" | "out_of_stock" | "discontinued";

export interface InventoryItem {
  substance: string;
  vial_size_mg: number;
  status: InventoryStatus;
  lot_number?: string;
  last_sync?: string;
}

// ─── Billing ───
export interface CheckoutResult {
  session_id: string;
  url: string;
  mode: "live" | "mock";
}
