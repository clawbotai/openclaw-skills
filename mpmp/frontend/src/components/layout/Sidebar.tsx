"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";
import { useAuth } from "@/stores/auth";

const providerNav = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/patients", label: "Patients", icon: "👥" },
  { href: "/appointments", label: "Schedule", icon: "📅" },
  { href: "/calculator", label: "Calculator", icon: "🧮" },
  { href: "/notes", label: "Notes", icon: "📋" },
  { href: "/billing", label: "Billing", icon: "💳" },
];

const adminNav = [
  ...providerNav,
  { href: "/admin", label: "Admin", icon: "⚙️" },
];

const patientNav = [
  { href: "/portal", label: "My Health", icon: "❤️" },
  { href: "/portal/appointments", label: "Appointments", icon: "📅" },
  { href: "/portal/billing", label: "Payments", icon: "💳" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  if (!user) return null;

  const nav =
    user.role === "superadmin"
      ? adminNav
      : user.role === "patient"
      ? patientNav
      : providerNav;

  return (
    <aside className="fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-gray-200 bg-white">
      {/* Brand */}
      <div className="flex h-16 items-center border-b border-gray-200 px-6">
        <span className="text-xl font-bold text-brand-700">MPMP</span>
        <span className="ml-2 text-xs text-gray-400">v0.1</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        {nav.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={clsx(
              "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
              pathname === item.href || pathname.startsWith(item.href + "/")
                ? "bg-brand-50 text-brand-700"
                : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
            )}
          >
            <span className="text-lg">{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>

      {/* User info + logout */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-100 text-sm font-bold text-brand-700">
            {user.email[0].toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="truncate text-sm font-medium text-gray-900">
              {user.email}
            </p>
            <p className="text-xs capitalize text-gray-500">
              {user.role.replace("_", " ")}
            </p>
          </div>
        </div>
        <button
          onClick={logout}
          className="mt-3 w-full rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 transition-colors"
        >
          Sign Out
        </button>
      </div>
    </aside>
  );
}
