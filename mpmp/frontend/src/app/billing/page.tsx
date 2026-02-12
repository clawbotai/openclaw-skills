"use client";
import Header from "@/components/layout/Header";

export default function BillingPage() {
  return (
    <>
      <Header title="Billing" />
      <div className="p-6">
        <div className="card">
          <h3 className="mb-4 text-lg font-semibold">Payment Overview</h3>
          <p className="text-sm text-gray-500">
            Stripe integration ready. Configure <code className="rounded bg-gray-100 px-1.5 py-0.5 text-xs">STRIPE_SECRET_KEY</code> to enable live payments.
          </p>
          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded-lg bg-green-50 p-4">
              <p className="text-2xl font-bold text-medical-green">$0</p>
              <p className="text-xs text-gray-500">Collected this month</p>
            </div>
            <div className="rounded-lg bg-amber-50 p-4">
              <p className="text-2xl font-bold text-medical-amber">0</p>
              <p className="text-xs text-gray-500">Pending payments</p>
            </div>
            <div className="rounded-lg bg-blue-50 p-4">
              <p className="text-2xl font-bold text-medical-blue">0</p>
              <p className="text-xs text-gray-500">Active subscriptions</p>
            </div>
          </div>
        </div>

        <div className="card mt-6">
          <h3 className="mb-4 text-lg font-semibold">Workflow Gate</h3>
          <p className="text-sm text-gray-600">
            When enabled, the system holds Azoth MedicationRequest submissions until the patient&apos;s 
            Stripe invoice is marked as <span className="badge-green">PAID</span>.
          </p>
          <div className="mt-4 flex items-center gap-3">
            <div className="h-4 w-8 rounded-full bg-gray-200" />
            <span className="text-sm text-gray-500">Payment gate disabled (no Stripe key)</span>
          </div>
        </div>
      </div>
    </>
  );
}
