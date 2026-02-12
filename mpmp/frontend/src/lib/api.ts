/**
 * API client — handles token refresh, error normalization, and type-safe requests.
 */
const API_BASE = "/api/v1";

let accessToken: string | null = null;
let refreshToken: string | null = null;

export function setTokens(access: string, refresh: string) {
  accessToken = access;
  refreshToken = refresh;
  if (typeof window !== "undefined") {
    sessionStorage.setItem("mpmp_access", access);
    sessionStorage.setItem("mpmp_refresh", refresh);
  }
}

export function loadTokens() {
  if (typeof window !== "undefined") {
    accessToken = sessionStorage.getItem("mpmp_access");
    refreshToken = sessionStorage.getItem("mpmp_refresh");
  }
}

export function clearTokens() {
  accessToken = null;
  refreshToken = null;
  if (typeof window !== "undefined") {
    sessionStorage.removeItem("mpmp_access");
    sessionStorage.removeItem("mpmp_refresh");
  }
}

export function getAccessToken() {
  return accessToken;
}

class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function refreshAccessToken(): Promise<boolean> {
  if (!refreshToken) return false;
  try {
    const resp = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!resp.ok) return false;
    const data = await resp.json();
    setTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

export async function api<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  loadTokens();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  let resp = await fetch(`${API_BASE}${path}`, { ...options, headers });

  // Auto-refresh on 401
  if (resp.status === 401 && refreshToken) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      headers["Authorization"] = `Bearer ${accessToken}`;
      resp = await fetch(`${API_BASE}${path}`, { ...options, headers });
    }
  }

  if (!resp.ok) {
    const body = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new ApiError(resp.status, body.detail || resp.statusText);
  }

  return resp.json();
}

// ─── Typed API methods ───
import type {
  TokenPair,
  User,
  Patient,
  PatientListItem,
  ClinicalNote,
  SOAPData,
  Appointment,
  DosageResult,
  PeptidePreset,
  InventoryItem,
} from "@/types";

export const auth = {
  login: (email: string, password: string) =>
    api<TokenPair>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  register: (email: string, password: string) =>
    api<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => api<User>("/auth/me"),
};

export const patients = {
  list: (limit = 50, offset = 0) =>
    api<PatientListItem[]>(`/patients/?limit=${limit}&offset=${offset}`),
  get: (id: string) => api<Patient>(`/patients/${id}`),
  myProfile: () => api<Patient>("/patients/me"),
  create: (data: Record<string, unknown>) =>
    api<Patient>("/patients/", { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: Record<string, unknown>) =>
    api<Patient>(`/patients/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
};

export const clinical = {
  create: (patient_id: string, soap: SOAPData) =>
    api<ClinicalNote>("/clinical-notes/", {
      method: "POST",
      body: JSON.stringify({ patient_id, soap }),
    }),
  getForPatient: (patient_id: string) =>
    api<ClinicalNote[]>(`/clinical-notes/patient/${patient_id}`),
  get: (id: string) => api<ClinicalNote>(`/clinical-notes/${id}`),
  update: (id: string, soap: SOAPData) =>
    api<ClinicalNote>(`/clinical-notes/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ soap }),
    }),
  sign: (id: string) =>
    api<ClinicalNote>(`/clinical-notes/${id}/sign`, { method: "POST" }),
};

export const appointments = {
  list: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return api<Appointment[]>(`/appointments/${qs}`);
  },
  get: (id: string) => api<Appointment>(`/appointments/${id}`),
  create: (data: Record<string, unknown>) =>
    api<Appointment>("/appointments/", { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: Record<string, unknown>) =>
    api<Appointment>(`/appointments/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  cancel: (id: string) =>
    api<Appointment>(`/appointments/${id}`, { method: "DELETE" }),
};

export const calculator = {
  calculate: (data: Record<string, unknown>) =>
    api<DosageResult>("/calculator/calculate", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  presets: () => api<PeptidePreset[]>("/calculator/presets"),
};

export const inventory = {
  list: () => api<InventoryItem[]>("/webhooks/inventory"),
};
