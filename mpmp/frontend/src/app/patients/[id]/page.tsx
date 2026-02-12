"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Header from "@/components/layout/Header";
import { patients as patientsApi, clinical } from "@/lib/api";
import type { Patient, ClinicalNote } from "@/types";

export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [notes, setNotes] = useState<ClinicalNote[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [pt, n] = await Promise.all([
          patientsApi.get(id),
          clinical.getForPatient(id),
        ]);
        setPatient(pt);
        setNotes(n);
      } catch {}
      setLoading(false);
    };
    load();
  }, [id]);

  if (loading) {
    return (
      <>
        <Header title="Patient" />
        <div className="flex items-center justify-center p-12 text-gray-400">Loading…</div>
      </>
    );
  }

  if (!patient) {
    return (
      <>
        <Header title="Patient Not Found" />
        <div className="p-6 text-gray-500">Patient not found</div>
      </>
    );
  }

  return (
    <>
      <Header title={`${patient.first_name} ${patient.last_name}`} />
      <div className="p-6 space-y-6">
        {/* Patient Info */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="card lg:col-span-2">
            <h3 className="mb-4 text-lg font-semibold">Demographics</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <InfoRow label="First Name" value={patient.first_name} />
              <InfoRow label="Last Name" value={patient.last_name} />
              <InfoRow label="Date of Birth" value={patient.dob} />
              <InfoRow label="Azoth Alias" value={patient.azoth_alias_id.slice(0, 12) + "…"} mono />
              <InfoRow label="Weight" value={patient.weight_kg ? `${patient.weight_kg} kg` : "—"} />
              <InfoRow label="Height" value={patient.height_cm ? `${patient.height_cm} cm` : "—"} />
              {patient.bmi && <InfoRow label="BMI" value={patient.bmi.toFixed(1)} />}
            </div>
          </div>

          <div className="card">
            <h3 className="mb-4 text-lg font-semibold">Quick Actions</h3>
            <div className="space-y-2">
              <button className="btn-primary w-full text-sm">📋 New SOAP Note</button>
              <button className="btn-secondary w-full text-sm">📅 Schedule Appointment</button>
              <button className="btn-secondary w-full text-sm">🧮 Calculate Dosage</button>
              <button className="btn-secondary w-full text-sm">💊 New Prescription</button>
            </div>
          </div>
        </div>

        {/* Clinical Notes */}
        <div className="card">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold">Clinical Notes</h3>
            <span className="text-sm text-gray-400">{notes.length} notes</span>
          </div>
          {notes.length === 0 ? (
            <p className="text-sm text-gray-400">No clinical notes yet</p>
          ) : (
            <div className="space-y-3">
              {notes.map((note) => (
                <div
                  key={note.id}
                  className="rounded-lg border border-gray-100 p-4"
                >
                  <div className="mb-2 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-900">
                        v{note.version}
                      </span>
                      {note.signed_at ? (
                        <span className="badge-green">✓ Signed</span>
                      ) : (
                        <span className="badge-amber">Draft</span>
                      )}
                    </div>
                    <span className="text-xs text-gray-400">
                      {new Date(note.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <SOAPSection label="S" title="Subjective" text={note.soap.subjective} />
                    <SOAPSection label="O" title="Objective" text={note.soap.objective} />
                    <SOAPSection label="A" title="Assessment" text={note.soap.assessment} />
                    <SOAPSection label="P" title="Plan" text={note.soap.plan} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function InfoRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`font-medium text-gray-900 ${mono ? "font-mono text-xs" : ""}`}>
        {value}
      </p>
    </div>
  );
}

function SOAPSection({ label, title, text }: { label: string; title: string; text: string }) {
  return (
    <div className="rounded-lg bg-gray-50 p-3">
      <div className="mb-1 flex items-center gap-2">
        <span className="flex h-5 w-5 items-center justify-center rounded bg-brand-100 text-xs font-bold text-brand-700">
          {label}
        </span>
        <span className="text-xs font-medium text-gray-500">{title}</span>
      </div>
      <p className="text-sm text-gray-700">{text || "—"}</p>
    </div>
  );
}
