import { create } from "zustand";
import type { InventoryItem } from "@/types";
import { inventory as invApi } from "@/lib/api";

interface InventoryState {
  items: InventoryItem[];
  loading: boolean;
  wsConnected: boolean;
  fetch: () => Promise<void>;
  connectWebSocket: () => void;
  updateItem: (item: InventoryItem) => void;
}

export const useInventory = create<InventoryState>((set, get) => ({
  items: [],
  loading: false,
  wsConnected: false,

  fetch: async () => {
    set({ loading: true });
    try {
      const items = await invApi.list();
      set({ items, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  connectWebSocket: () => {
    if (get().wsConnected) return;
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${window.location.host}/ws/inventory`);

    ws.onopen = () => set({ wsConnected: true });
    ws.onclose = () => {
      set({ wsConnected: false });
      // Reconnect after 5s
      setTimeout(() => get().connectWebSocket(), 5000);
    };
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "inventory_update" && data.data) {
          get().updateItem(data.data);
        }
      } catch {}
    };
  },

  updateItem: (updated) => {
    set((state) => {
      const idx = state.items.findIndex(
        (i) =>
          i.substance === updated.substance &&
          i.vial_size_mg === updated.vial_size_mg
      );
      const items = [...state.items];
      if (idx >= 0) {
        items[idx] = updated;
      } else {
        items.push(updated);
      }
      return { items };
    });
  },
}));
