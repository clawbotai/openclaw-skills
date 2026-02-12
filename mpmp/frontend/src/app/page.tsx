"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/stores/auth";

export default function Home() {
  const router = useRouter();
  const { user, loading, checkAuth } = useAuth();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    if (!loading) {
      if (!user) {
        router.replace("/auth");
      } else if (user.role === "patient") {
        router.replace("/portal");
      } else {
        router.replace("/dashboard");
      }
    }
  }, [user, loading, router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="animate-pulse text-gray-400">Loading…</div>
    </div>
  );
}
