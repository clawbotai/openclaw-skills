"use client";
import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import { calculator as calcApi } from "@/lib/api";
import { useInventory } from "@/stores/inventory";
import type { DosageResult, PeptidePreset } from "@/types";

export default function CalculatorPage() {
  const { items: inventory, fetch: fetchInventory } = useInventory();
  const [presets, setPresets] = useState<PeptidePreset[]>([]);
  const [result, setResult] = useState<DosageResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Form state
  const [compound, setCompound] = useState("");
  const [vialSize, setVialSize] = useState("");
  const [diluent, setDiluent] = useState("2");
  const [syringe, setSyringe] = useState("U-100 1mL Insulin Syringe");
  const [targetDose, setTargetDose] = useState("");
  const [route, setRoute] = useState("subcutaneous");
  const [frequency, setFrequency] = useState("daily");

  useEffect(() => {
    calcApi.presets().then(setPresets).catch(() => {});
    fetchInventory();
  }, [fetchInventory]);

  const applyPreset = (preset: PeptidePreset) => {
    setCompound(preset.name);
    setVialSize(preset.typical_vial_mg.toString());
    setTargetDose(preset.typical_dose_mcg.toString());
    setRoute(preset.route);
  };

  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const r = await calcApi.calculate({
        compound,
        vial_size_mg: parseFloat(vialSize),
        diluent_ml: parseFloat(diluent),
        syringe_type: syringe,
        target_dose_mcg: parseFloat(targetDose),
        route,
        frequency,
      });
      setResult(r);
    } catch (e: any) {
      setError(e.detail || "Calculation failed");
    }
    setLoading(false);
  };

  // Check inventory availability
  const vialAvailable = compound
    ? inventory.find(
        (i) =>
          i.substance.toLowerCase() === compound.toLowerCase() &&
          i.vial_size_mg === parseFloat(vialSize)
      )
    : null;
  const isOutOfStock = vialAvailable?.status === "out_of_stock";

  return (
    <>
      <Header title="Magistral Dosage Calculator" />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Input Form */}
          <div className="card lg:col-span-2">
            <h3 className="mb-4 text-lg font-semibold">Reconstitution Calculator</h3>

            {/* Presets */}
            <div className="mb-6">
              <p className="mb-2 text-xs font-medium text-gray-500">Quick Presets</p>
              <div className="flex flex-wrap gap-2">
                {presets.map((p) => (
                  <button
                    key={p.name}
                    onClick={() => applyPreset(p)}
                    className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
                      compound === p.name
                        ? "border-brand-500 bg-brand-50 text-brand-700"
                        : "border-gray-200 text-gray-600 hover:border-gray-300"
                    }`}
                  >
                    {p.name}
                  </button>
                ))}
              </div>
            </div>

            <form onSubmit={handleCalculate} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Compound
                  </label>
                  <input
                    value={compound}
                    onChange={(e) => setCompound(e.target.value)}
                    className="input-field"
                    placeholder="BPC-157"
                    required
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Vial Size (mg)
                    {isOutOfStock && (
                      <span className="ml-2 text-xs text-medical-red">⚠ Out of stock</span>
                    )}
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={vialSize}
                    onChange={(e) => setVialSize(e.target.value)}
                    className={`input-field ${isOutOfStock ? "border-medical-red bg-red-50" : ""}`}
                    placeholder="5"
                    required
                    disabled={isOutOfStock}
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Diluent Volume (mL)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={diluent}
                    onChange={(e) => setDiluent(e.target.value)}
                    className="input-field"
                    placeholder="2"
                    required
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Target Dose (mcg)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={targetDose}
                    onChange={(e) => setTargetDose(e.target.value)}
                    className="input-field"
                    placeholder="250"
                    required
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Syringe Type
                  </label>
                  <select
                    value={syringe}
                    onChange={(e) => setSyringe(e.target.value)}
                    className="input-field"
                  >
                    <option>U-100 1mL Insulin Syringe</option>
                    <option>U-100 0.5mL Insulin Syringe</option>
                    <option>U-50 Syringe</option>
                    <option>U-40 Syringe</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Route
                  </label>
                  <select
                    value={route}
                    onChange={(e) => setRoute(e.target.value)}
                    className="input-field"
                  >
                    <option value="subcutaneous">Subcutaneous</option>
                    <option value="intramuscular">Intramuscular</option>
                    <option value="intravenous">Intravenous</option>
                    <option value="oral">Oral</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Frequency
                </label>
                <select
                  value={frequency}
                  onChange={(e) => setFrequency(e.target.value)}
                  className="input-field w-48"
                >
                  <option value="daily">Daily</option>
                  <option value="twice daily">Twice Daily</option>
                  <option value="every other day">Every Other Day</option>
                  <option value="twice weekly">Twice Weekly</option>
                  <option value="weekly">Weekly</option>
                  <option value="as needed">As Needed</option>
                </select>
              </div>

              {error && (
                <div className="rounded-lg bg-red-50 p-3 text-sm text-medical-red">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading || isOutOfStock}
                className="btn-primary"
              >
                {loading ? "Calculating…" : "🧮 Calculate Dosage"}
              </button>
            </form>
          </div>

          {/* Result Panel */}
          <div className="card">
            <h3 className="mb-4 text-lg font-semibold">Result</h3>
            {result ? (
              <div className="space-y-4">
                <div className="rounded-xl bg-brand-50 p-4">
                  <p className="text-3xl font-bold text-brand-800">
                    {result.syringe_units.toFixed(0)} Units
                  </p>
                  <p className="text-sm text-brand-600">
                    {result.draw_volume_ml.toFixed(2)} mL draw volume
                  </p>
                </div>

                <div className="space-y-2 text-sm">
                  <ResultRow label="Concentration" value={`${result.concentration_mcg_per_ml.toFixed(1)} mcg/mL`} />
                  <ResultRow label="Doses per Vial" value={result.doses_per_vial.toString()} />
                  <ResultRow label="Total Mass" value={`${result.total_mass_mcg.toFixed(0)} mcg`} />
                </div>

                <div className="rounded-lg border border-brand-200 bg-brand-50/50 p-3">
                  <p className="mb-1 text-xs font-medium text-brand-700">
                    Patient Instructions
                  </p>
                  <p className="text-sm text-brand-900">{result.human_readable}</p>
                </div>

                <div className="rounded-lg bg-gray-50 p-3">
                  <p className="mb-1 text-xs font-medium text-gray-500">
                    FHIR Dosage Text
                  </p>
                  <p className="font-mono text-xs text-gray-600">
                    {result.fhir_dosage_text}
                  </p>
                </div>

                <button className="btn-primary w-full text-sm">
                  💊 Create Prescription with This Dosage
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center py-12 text-gray-300">
                <span className="text-5xl">🧮</span>
                <p className="mt-3 text-sm">Enter parameters and calculate</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

function ResultRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-gray-900">{value}</span>
    </div>
  );
}
