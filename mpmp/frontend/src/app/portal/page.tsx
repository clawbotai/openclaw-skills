"use client";
import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import { patients as patientsApi } from "@/lib/api";
import type { Patient } from "@/types";

export default function PatientPortalPage() {
  const [profile, setProfile] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    patientsApi.myProfile().then(setProfile).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <>
        <Header title="My Health" />
        <div className="flex items-center justify-center p-12 text-gray-400">Loading…</div>
      </>
    );
  }

  return (
    <>
      <Header title="My Health Dashboard" />
      <div className="p-6 space-y-6">
        {profile ? (
          <>
            {/* Welcome Card */}
            <div className="card bg-gradient-to-r from-brand-50 to-blue-50">
              <h2 className="text-2xl font-bold text-gray-900">
                Welcome back, {profile.first_name}
              </h2>
              <p className="mt-1 text-sm text-gray-500">
                Here's your health overview
              </p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              {profile.weight_kg && (
                <div className="card text-center">
                  <p className="text-3xl font-bold text-gray-900">{profile.weight_kg}</p>
                  <p className="text-xs text-gray-500">Weight (kg)</p>
                </div>
              )}
              {profile.bmi && (
                <div className="card text-center">
                  <p className="text-3xl font-bold text-gray-900">{profile.bmi.toFixed(1)}</p>
                  <p className="text-xs text-gray-500">BMI</p>
                </div>
              )}
              {profile.height_cm && (
                <div className="card text-center">
                  <p className="text-3xl font-bold text-gray-900">{profile.height_cm}</p>
                  <p className="text-xs text-gray-500">Height (cm)</p>
                </div>
              )}
            </div>

            {/* Active Protocols */}
            <div className="card">
              <h3 className="mb-4 text-lg font-semibold">Active Protocols</h3>
              <p className="text-sm text-gray-400">
                No active protocols yet. Your provider will prescribe your treatment plan.
              </p>
            </div>

            {/* Shipment Tracking */}
            <div className="card">
              <h3 className="mb-4 text-lg font-semibold">📦 Shipment Tracking</h3>
              <p className="text-sm text-gray-400">
                No active shipments. Tracking information will appear here once your order is processed through Azoth OS.
              </p>
            </div>

            {/* Dosage Instructions */}
            <div className="card">
              <h3 className="mb-4 text-lg font-semibold">💉 Dosage Instructions</h3>
              <p className="text-sm text-gray-400">
                Dosage instruction videos and guides will appear here when prescribed by your provider.
              </p>
            </div>
          </>
        ) : (
          <div className="card">
            <p className="text-sm text-gray-500">
              No patient profile found. Please contact your provider.
            </p>
          </div>
        )}
      </div>
    </>
  );
}
