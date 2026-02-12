"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import { patients as patientsApi } from "@/lib/api";
import type { PatientListItem } from "@/types";

export default function PatientsPage() {
  const [list, setList] = useState<PatientListItem[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    patientsApi.list(200, 0).then(setList).finally(() => setLoading(false));
  }, []);

  const filtered = list.filter(
    (p) =>
      p.first_name.toLowerCase().includes(search.toLowerCase()) ||
      p.last_name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <>
      <Header title="Patients" />
      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <input
            type="text"
            placeholder="Search patients…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input-field w-80"
          />
          <Link href="/patients/new" className="btn-primary">
            + New Patient
          </Link>
        </div>

        <div className="card overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-4 py-3 text-left font-medium text-gray-500">Name</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Azoth Alias</th>
                <th className="px-4 py-3 text-right font-medium text-gray-500">Weight (kg)</th>
                <th className="px-4 py-3 text-right font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                    Loading…
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                    {search ? "No matches" : "No patients yet"}
                  </td>
                </tr>
              ) : (
                filtered.map((pt) => (
                  <tr key={pt.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3">
                      <Link
                        href={`/patients/${pt.id}`}
                        className="font-medium text-gray-900 hover:text-brand-600"
                      >
                        {pt.first_name} {pt.last_name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-400">
                      {pt.azoth_alias_id.slice(0, 12)}…
                    </td>
                    <td className="px-4 py-3 text-right text-gray-600">
                      {pt.weight_kg ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link
                        href={`/patients/${pt.id}`}
                        className="text-xs font-medium text-brand-600 hover:underline"
                      >
                        View →
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
