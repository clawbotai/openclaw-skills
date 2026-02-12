"use client";
import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import { appointments as aptApi } from "@/lib/api";
import type { Appointment } from "@/types";

export default function AppointmentsPage() {
  const [apts, setApts] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<"list" | "today">("today");

  useEffect(() => {
    const load = async () => {
      const params: Record<string, string> = {};
      if (view === "today") {
        const today = new Date().toISOString().split("T")[0];
        params.from_date = `${today}T00:00:00`;
        params.to_date = `${today}T23:59:59`;
      }
      try {
        const data = await aptApi.list(params);
        setApts(data);
      } catch {}
      setLoading(false);
    };
    load();
  }, [view]);

  const statusColor: Record<string, string> = {
    scheduled: "bg-blue-100 text-blue-700",
    checked_in: "bg-amber-100 text-amber-700",
    in_progress: "bg-green-100 text-green-700",
    completed: "bg-gray-100 text-gray-600",
    cancelled: "bg-red-100 text-red-700",
    no_show: "bg-red-100 text-red-700",
  };

  return (
    <>
      <Header title="Schedule" />
      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            <button
              onClick={() => setView("today")}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
                view === "today" ? "bg-brand-100 text-brand-700" : "text-gray-500 hover:bg-gray-100"
              }`}
            >
              Today
            </button>
            <button
              onClick={() => setView("list")}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
                view === "list" ? "bg-brand-100 text-brand-700" : "text-gray-500 hover:bg-gray-100"
              }`}
            >
              All Upcoming
            </button>
          </div>
          <button className="btn-primary">+ New Appointment</button>
        </div>

        <div className="card overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-4 py-3 text-left font-medium text-gray-500">Time</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Patient</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Duration</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Status</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Telehealth</th>
                <th className="px-4 py-3 text-right font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-400">Loading…</td>
                </tr>
              ) : apts.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                    No appointments {view === "today" ? "today" : "found"}
                  </td>
                </tr>
              ) : (
                apts.map((apt) => (
                  <tr key={apt.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">
                      {new Date(apt.start_time).toLocaleTimeString("en-US", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">
                      {apt.patient_id.slice(0, 8)}…
                    </td>
                    <td className="px-4 py-3 text-gray-600">{apt.duration_minutes}min</td>
                    <td className="px-4 py-3">
                      <span className={`badge ${statusColor[apt.status] || "badge-gray"}`}>
                        {apt.status.replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {apt.telehealth_link ? (
                        <a
                          href={apt.telehealth_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-brand-600 hover:underline"
                        >
                          🎥 Join
                        </a>
                      ) : (
                        <span className="text-xs text-gray-300">In-person</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button className="text-xs text-gray-500 hover:text-gray-700">
                        Edit
                      </button>
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
