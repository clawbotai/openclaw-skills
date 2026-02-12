"use client";
import { useInventory } from "@/stores/inventory";

export default function Header({ title }: { title: string }) {
  const { wsConnected } = useInventory();

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-gray-200 bg-white/80 px-6 backdrop-blur-sm">
      <h1 className="text-lg font-semibold text-gray-900">{title}</h1>
      <div className="flex items-center gap-4">
        {/* Azoth connection indicator */}
        <div className="flex items-center gap-2 text-xs">
          <span
            className={`h-2 w-2 rounded-full ${
              wsConnected ? "bg-medical-green" : "bg-gray-300"
            }`}
          />
          <span className="text-gray-500">
            {wsConnected ? "Azoth Live" : "Standalone"}
          </span>
        </div>
      </div>
    </header>
  );
}
