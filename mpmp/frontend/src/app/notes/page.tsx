"use client";
import { useState } from "react";
import Header from "@/components/layout/Header";
import { clinical } from "@/lib/api";
import type { ClinicalNote, SOAPData } from "@/types";

export default function NotesPage() {
  const [patientId, setPatientId] = useState("");
  const [notes, setNotes] = useState<ClinicalNote[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreate, setShowCreate] = useState(false);

  // Create form
  const [soap, setSoap] = useState<SOAPData>({
    subjective: "",
    objective: "",
    assessment: "",
    plan: "",
  });
  const [creating, setCreating] = useState(false);

  const loadNotes = async () => {
    if (!patientId) return;
    setLoading(true);
    try {
      const data = await clinical.getForPatient(patientId);
      setNotes(data);
    } catch {}
    setLoading(false);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!patientId) return;
    setCreating(true);
    try {
      await clinical.create(patientId, soap);
      setSoap({ subjective: "", objective: "", assessment: "", plan: "" });
      setShowCreate(false);
      await loadNotes();
    } catch {}
    setCreating(false);
  };

  const handleSign = async (noteId: string) => {
    if (!confirm("Sign this note? Signed notes are immutable.")) return;
    try {
      await clinical.sign(noteId);
      await loadNotes();
    } catch {}
  };

  return (
    <>
      <Header title="Clinical Notes" />
      <div className="p-6 space-y-4">
        {/* Patient selector */}
        <div className="flex items-center gap-3">
          <input
            placeholder="Patient ID"
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            className="input-field w-80"
          />
          <button onClick={loadNotes} className="btn-secondary">
            Load Notes
          </button>
          <button onClick={() => setShowCreate(!showCreate)} className="btn-primary">
            + New SOAP Note
          </button>
        </div>

        {/* Create Form */}
        {showCreate && (
          <form onSubmit={handleCreate} className="card space-y-4">
            <h3 className="text-lg font-semibold">New SOAP Note</h3>
            {(["subjective", "objective", "assessment", "plan"] as const).map((field) => (
              <div key={field}>
                <label className="mb-1 block text-sm font-medium capitalize text-gray-700">
                  {field} ({field[0].toUpperCase()})
                </label>
                <textarea
                  value={soap[field]}
                  onChange={(e) => setSoap({ ...soap, [field]: e.target.value })}
                  className="input-field min-h-[80px]"
                  placeholder={`Enter ${field}…`}
                />
              </div>
            ))}
            <div className="flex gap-2">
              <button type="submit" disabled={creating} className="btn-primary">
                {creating ? "Saving…" : "Save Note"}
              </button>
              <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary">
                Cancel
              </button>
            </div>
          </form>
        )}

        {/* Notes List */}
        {loading ? (
          <p className="text-gray-400">Loading…</p>
        ) : (
          <div className="space-y-4">
            {notes.map((note) => (
              <div key={note.id} className="card">
                <div className="mb-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium">Version {note.version}</span>
                    {note.signed_at ? (
                      <span className="badge-green">✓ Signed {new Date(note.signed_at).toLocaleDateString()}</span>
                    ) : (
                      <>
                        <span className="badge-amber">Draft</span>
                        <button
                          onClick={() => handleSign(note.id)}
                          className="text-xs font-medium text-brand-600 hover:underline"
                        >
                          Sign Now
                        </button>
                      </>
                    )}
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(note.created_at).toLocaleString()}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {(["subjective", "objective", "assessment", "plan"] as const).map((field) => (
                    <div key={field} className="rounded-lg bg-gray-50 p-3">
                      <p className="mb-1 text-xs font-bold uppercase text-gray-400">
                        {field[0]} — {field}
                      </p>
                      <p className="text-sm text-gray-700">{note.soap[field] || "—"}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
