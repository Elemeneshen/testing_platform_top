import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type Language = 'ru' | 'en';

interface LanguageState {
  language: Language;
  setLanguage: (language: Language) => void;
}

export const useLanguageStore = create<LanguageState>()(persist((set) => ({
  language: 'ru',
  setLanguage: (language) => set({ language }),
}), { name: 'codeclass-language' }));

export const useTranslation = () => {
  const language = useLanguageStore((state) => state.language);
  return { language, t: (ru: string, en: string) => language === 'ru' ? ru : en };
};
