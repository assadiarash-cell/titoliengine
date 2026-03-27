import { create } from 'zustand';
import api from '../api/client';

interface AuthState {
  isAuthenticated: boolean;
  userId: string | null;
  studioId: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: !!localStorage.getItem('te_access_token'),
  userId: null,
  studioId: null,
  loading: false,

  login: async (email: string, password: string) => {
    set({ loading: true });
    try {
      const { data } = await api.post('/auth/login', { email, password });
      localStorage.setItem('te_access_token', data.access_token);
      localStorage.setItem('te_refresh_token', data.refresh_token);
      set({ isAuthenticated: true, userId: data.user_id, studioId: data.studio_id, loading: false });
    } catch {
      set({ loading: false });
      throw new Error('Credenziali non valide');
    }
  },

  logout: () => {
    localStorage.removeItem('te_access_token');
    localStorage.removeItem('te_refresh_token');
    set({ isAuthenticated: false, userId: null, studioId: null });
  },

  checkAuth: () => {
    const token = localStorage.getItem('te_access_token');
    set({ isAuthenticated: !!token });
  },
}));
