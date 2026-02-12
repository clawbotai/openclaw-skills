import { create } from "zustand";
import type { User } from "@/types";
import { auth as authApi, setTokens, clearTokens, loadTokens } from "@/lib/api";

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  loading: true,
  error: null,

  login: async (email, password) => {
    set({ loading: true, error: null });
    try {
      const tokens = await authApi.login(email, password);
      setTokens(tokens.access_token, tokens.refresh_token);
      const user = await authApi.me();
      set({ user, loading: false });
    } catch (e: any) {
      set({ error: e.detail || "Login failed", loading: false });
    }
  },

  logout: () => {
    clearTokens();
    set({ user: null, loading: false, error: null });
  },

  checkAuth: async () => {
    loadTokens();
    try {
      const user = await authApi.me();
      set({ user, loading: false });
    } catch {
      set({ user: null, loading: false });
    }
  },
}));
