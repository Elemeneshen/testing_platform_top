import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type ThemeId = 'midnight' | 'studio' | 'terminal' | 'aurora';

export const themes: Array<{
  id: ThemeId;
  name: string;
  description: string;
  colors: [string, string, string];
}> = [
  { id: 'midnight', name: 'Midnight', description: 'Deep violet workspace', colors: ['#090d13', '#171f2a', '#8b5cf6'] },
  { id: 'studio', name: 'Washi', description: 'Warm paper and terracotta', colors: ['#f4f1ec', '#eae5dc', '#9c4a3e'] },
  { id: 'terminal', name: 'Ronin Dark', description: 'Warm graphite and vermilion', colors: ['#1c1b1a', '#242220', '#b2564a'] },
  { id: 'aurora', name: 'Aurora', description: 'Cool glass and cyan', colors: ['#07131d', '#102634', '#20c7d9'] },
];

interface ThemeState {
  theme: ThemeId;
  setTheme: (theme: ThemeId) => void;
}

export const useThemeStore = create<ThemeState>()(persist((set) => ({
  theme: 'midnight',
  setTheme: (theme) => set({ theme }),
}), { name: 'codeclass-theme' }));
