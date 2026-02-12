"use client";
import { useState } from "react";
import Header from "@/components/layout/Header";
import { useInventory } from "@/stores/inventory";

export default function AdminPage() {
  const { items: inventory, wsConnected } = useInventory();
  const [azothSync, setAzothSync] = useState(false);

  return (
    <>
      <Header title="Administration" />
      <div className="p-6 space-y-6">
        {/* System Status */}
        <div className="card">
          <h3 className="mb-4 text-lg font-semibold">System Status</h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatusItem
              label="Database"
              status="connected"
              detail="PostgreSQL 16"
            />
            <StatusItem
              label="Redis"
              status="connected"
              detail="Session cache + job queue"
            />
            <StatusItem
              label="Azoth WebSocket"
              status={wsConnected ? "connected" : "disconnected"}
              detail={wsConnected ? "Receiving inventory updates" : "Standalone mode"}
            />
          </div>
        </div>

        {/* Azoth OS Toggle */}
        <div className="card">
          <h3 className="mb-4 text-lg font-semibold">Azoth OS Integration</h3>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">AZOTH_OS_SYNC</p>
              <p className="text-sm text-gray-500">
                {azothSync
                  ? "Connected Mode — orders routed via FHIR API, inventory from webhooks"
                  : "Standalone Mode — encrypted PDF via SMTP, local inventory"}
              </p>
            </div>
            <button
              onClick={() => setAzothSync(!azothSync)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                azothSync ? "bg-medical-green" : "bg-gray-300"
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  azothSync ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>
        </div>

        {/* API Keys */}
        <div className="card">
          <h3 className="mb-4 text-lg font-semibold">API Configuration</h3>
          <div className="space-y-3 text-sm">
            <ConfigRow label="AZOTH_CLIENT_ID" set={false} />
            <ConfigRow label="AZOTH_CLIENT_SECRET" set={false} />
            <ConfigRow label="AZOTH_WEBHOOK_SECRET" set={false} />
            <ConfigRow label="STRIPE_SECRET_KEY" set={false} />
            <ConfigRow label="SENDGRID_API_KEY" set={false} />
            <ConfigRow label="PHI_ENCRYPTION_KEY" set={true} />
          </div>
        </div>

        {/* Inventory Management */}
        <div className="card">
          <h3 className="mb-4 text-lg font-semibold">Inventory ({inventory.length} items)</h3>
          {inventory.length === 0 ? (
            <p className="text-sm text-gray-400">
              No inventory data. {azothSync ? "Waiting for webhook data…" : "Add items manually below."}
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="pb-2 text-left font-medium text-gray-500">Substance</th>
                    <th className="pb-2 text-left font-medium text-gray-500">Vial (mg)</th>
                    <th className="pb-2 text-left font-medium text-gray-500">Status</th>
                    <th className="pb-2 text-left font-medium text-gray-500">Lot #</th>
                    <th className="pb-2 text-left font-medium text-gray-500">Last Sync</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {inventory.map((item) => (
                    <tr key={`${item.substance}-${item.vial_size_mg}`}>
                      <td className="py-2 font-medium">{item.substance}</td>
                      <td className="py-2">{item.vial_size_mg}</td>
                      <td className="py-2">
                        <span className={
                          item.status === "in_stock" ? "badge-green" :
                          item.status === "low_stock" ? "badge-amber" :
                          item.status === "out_of_stock" ? "badge-red" : "badge-gray"
                        }>
                          {item.status.replace("_", " ")}
                        </span>
                      </td>
                      <td className="py-2 text-gray-500">{item.lot_number || "—"}</td>
                      <td className="py-2 text-xs text-gray-400">
                        {item.last_sync ? new Date(item.last_sync).toLocaleString() : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Audit Log Viewer */}
        <div className="card">
          <h3 className="mb-4 text-lg font-semibold">Audit Trail</h3>
          <p className="text-sm text-gray-400">
            HIPAA-compliant immutable audit log. Query via <code className="rounded bg-gray-100 px-1.5 py-0.5 text-xs">GET /api/v1/audit</code> endpoint (coming soon).
          </p>
        </div>
      </div>
    </>
  );
}

function StatusItem({ label, status, detail }: { label: string; status: string; detail: string }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-gray-100 p-3">
      <span className={`h-3 w-3 rounded-full ${status === "connected" ? "bg-medical-green" : "bg-gray-300"}`} />
      <div>
        <p className="text-sm font-medium text-gray-900">{label}</p>
        <p className="text-xs text-gray-500">{detail}</p>
      </div>
    </div>
  );
}

function ConfigRow({ label, set }: { label: string; set: boolean }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-gray-100 p-3">
      <code className="text-xs text-gray-600">{label}</code>
      {set ? (
        <span className="badge-green">Configured</span>
      ) : (
        <span className="badge-gray">Not set</span>
      )}
    </div>
  );
}
