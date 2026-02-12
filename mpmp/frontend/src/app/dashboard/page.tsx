"use client";
import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import { useAuth } from "@/stores/auth";
import { useInventory } from "@/stores/inventory";
import { patients as patientsApi, appointments as aptApi } from "@/lib/api";
import type { PatientListItem, Appointment } from "@/types";

export default function DashboardPage() {
  const { user } = useAuth();
  const { items: inventoryItems, fetch: fetchInventory } = useInventory();
  const [patientCount, setPatientCount] = useState(0);
  const [todayApts, setTodayApts] = useState<Appointment[]>([]);
  const [recentPatients, setRecentPatients] = useState<PatientListItem[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const pts = await patientsApi.list(5, 0);
        setRecentPatients(pts);
        setPatientCount(pts.length);

        const today = new Date().toISOString().split("T")[0];
        const apts = await aptApi.list({ from_date: `${today}T00:00:00`, to_date: `${today}T23:59:59` });
        setTodayApts(apts);

        await fetchInventory();
      } catch {}
    };
    load();
  }, [fetchInventory]);

  const outOfStock = inventoryItems.filter((i) => i.status === "out_of_stock");
  const lowStock = inventoryItems.filter((i) => i.status === "low_stock");

  return (
    <>
      <Header title="Dashboard" />
      <div className="p-6 space-y-6">
        {/* Welcome */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            Good {new Date().getHours() < 12 ? "morning" : new Date().getHours() < 18 ? "afternoon" : "evening"}, Dr.
          </h2>
          <p className="text-sm text-gray-500">
            {new Date().toLocaleDateString("en-US", {
              weekday: "long",
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            icon="👥"
            label="Active Patients"
            value={patientCount.toString()}
            color="brand"
          />
          <StatCard
            icon="📅"
            label="Today's Appointments"
            value={todayApts.length.toString()}
            color="blue"
          />
          <StatCard
            icon="📦"
            label="Inventory Items"
            value={inventoryItems.length.toString()}
            color="green"
            alert={outOfStock.length > 0 ? `${outOfStock.length} out of stock` : undefined}
          />
          <StatCard
            icon="⚠️"
            label="Alerts"
            value={(outOfStock.length + lowStock.length).toString()}
            color={outOfStock.length > 0 ? "red" : "gray"}
          />
        </div>

        {/* Two-column layout */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Today's Schedule */}
          <div className="card">
            <h3 className="mb-4 text-lg font-semibold text-gray-900">
              📅 Today's Schedule
            </h3>
            {todayApts.length === 0 ? (
              <p className="text-sm text-gray-400">No appointments today</p>
            ) : (
              <div className="space-y-3">
                {todayApts.map((apt) => (
                  <div
                    key={apt.id}
                    className="flex items-center justify-between rounded-lg border border-gray-100 p-3"
                  >
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {new Date(apt.start_time).toLocaleTimeString("en-US", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                      <p className="text-xs text-gray-500">
                        {apt.duration_minutes}min · Patient {apt.patient_id.slice(0, 8)}…
                      </p>
                    </div>
                    <StatusBadge status={apt.status} />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Inventory Alerts */}
          <div className="card">
            <h3 className="mb-4 text-lg font-semibold text-gray-900">
              📦 Inventory Status
            </h3>
            {inventoryItems.length === 0 ? (
              <p className="text-sm text-gray-400">No inventory data yet</p>
            ) : (
              <div className="space-y-2">
                {inventoryItems.slice(0, 8).map((item) => (
                  <div
                    key={`${item.substance}-${item.vial_size_mg}`}
                    className="flex items-center justify-between rounded-lg border border-gray-100 p-3"
                  >
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {item.substance}
                      </p>
                      <p className="text-xs text-gray-500">
                        {item.vial_size_mg}mg vial
                        {item.lot_number ? ` · Lot ${item.lot_number}` : ""}
                      </p>
                    </div>
                    <InventoryBadge status={item.status} />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Patients */}
        <div className="card">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">
            👥 Recent Patients
          </h3>
          {recentPatients.length === 0 ? (
            <p className="text-sm text-gray-400">No patients yet</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="pb-2 text-left font-medium text-gray-500">Name</th>
                    <th className="pb-2 text-left font-medium text-gray-500">Alias ID</th>
                    <th className="pb-2 text-right font-medium text-gray-500">Weight</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {recentPatients.map((pt) => (
                    <tr key={pt.id} className="hover:bg-gray-50">
                      <td className="py-2 font-medium text-gray-900">
                        {pt.first_name} {pt.last_name}
                      </td>
                      <td className="py-2 font-mono text-xs text-gray-400">
                        {pt.azoth_alias_id.slice(0, 8)}…
                      </td>
                      <td className="py-2 text-right text-gray-600">
                        {pt.weight_kg ? `${pt.weight_kg} kg` : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function StatCard({
  icon,
  label,
  value,
  color,
  alert,
}: {
  icon: string;
  label: string;
  value: string;
  color: string;
  alert?: string;
}) {
  const bgMap: Record<string, string> = {
    brand: "bg-brand-50",
    blue: "bg-blue-50",
    green: "bg-green-50",
    red: "bg-red-50",
    gray: "bg-gray-50",
  };

  return (
    <div className="card">
      <div className="flex items-center gap-3">
        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${bgMap[color] || bgMap.gray} text-xl`}>
          {icon}
        </div>
        <div>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <p className="text-xs text-gray-500">{label}</p>
        </div>
      </div>
      {alert && (
        <p className="mt-2 text-xs font-medium text-medical-red">{alert}</p>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    scheduled: "badge-blue",
    checked_in: "badge-amber",
    in_progress: "badge-green",
    completed: "badge-gray",
    cancelled: "badge-red",
    no_show: "badge-red",
  };
  return <span className={map[status] || "badge-gray"}>{status.replace("_", " ")}</span>;
}

function InventoryBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    in_stock: "badge-green",
    low_stock: "badge-amber",
    out_of_stock: "badge-red",
    discontinued: "badge-gray",
  };
  return <span className={map[status] || "badge-gray"}>{status.replace("_", " ")}</span>;
}
