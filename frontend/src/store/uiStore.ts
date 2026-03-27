import { create } from 'zustand';

interface UiState {
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  currentClientId: string | null;
  setCurrentClient: (id: string | null) => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  currentClientId: localStorage.getItem('te_current_client'),
  setCurrentClient: (id) => {
    if (id) localStorage.setItem('te_current_client', id);
    else localStorage.removeItem('te_current_client');
    set({ currentClientId: id });
  },
}));
