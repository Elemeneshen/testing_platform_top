import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  role: 'student' | 'teacher' | null;
  isAuthenticated: boolean;
  login: (role: 'student' | 'teacher') => void;
  logout: () => void;
  setRole: (role: 'student' | 'teacher' | null) => void;
}

export const useAuthStore = create<AuthState>()(persist((set) => ({
  role: null,
  isAuthenticated: false,
  login: (role) => set({ role, isAuthenticated: true }),
  logout: () => set({ role: null, isAuthenticated: false }),
  setRole: (role) => set({ role, isAuthenticated: role !== null })
}), { name: 'codeclass-auth' }));
