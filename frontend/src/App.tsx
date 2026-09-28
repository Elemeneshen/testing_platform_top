import { useEffect } from 'react';
import { BrowserRouter, useLocation } from 'react-router-dom';
import AppRoutes from './routes';
import { useThemeStore } from './store/themeStore';
import { useLanguageStore } from './store/languageStore';
import './App.css';
import './themes.css';

const pageTitles: Array<[RegExp, string, string]> = [
  [/^\/teacher\/teams\/[^/]+\/?$/, 'Доска команды', 'Team board'],
  [/^\/student\/teams\/[^/]+\/?$/, 'Доска команды', 'Team board'],
  [/^\/teacher\/teams\/?$/, 'Командные доски', 'Team boards'],
  [/^\/student\/teams\/?$/, 'Моя команда', 'My team'],
  [/^\/teacher\/task\/[^/]+\/review\/[^/]+\/?$/, 'Проверка кода', 'Code review'],
  [/^\/teacher\/task\/[^/]+\/?$/, 'Прогресс задачи', 'Task progress'],
  [/^\/teacher\/tests\/create\/?$/, 'Создание задачи', 'Create task'],
  [/^\/teacher\/dashboard\/?$/, 'Кабинет учителя', 'Teacher dashboard'],
  [/^\/teacher\/login\/?$/, 'Вход для учителя', 'Teacher login'],
  [/^\/student\/group\/?$/, 'Выбор группы', 'Choose group'],
  [/^\/register\/?$/, 'Регистрация ученика', 'Student registration'],
  [/^\/task\/[^/]+\/?$/, 'Задание', 'Assignment'],
  [/^\/test\/?$/, 'Мои задания', 'My tasks'],
  [/^\/login\/?$/, 'Вход для ученика', 'Student login'],
];

function PageTitle() {
  const { pathname } = useLocation();
  const language = useLanguageStore((state) => state.language);

  useEffect(() => {
    const match = pageTitles.find(([pattern]) => pattern.test(pathname));
    const section = match?.[language === 'ru' ? 1 : 2];
    document.title = section
      ? `${section} · Siberian Livecoding`
      : 'Siberian Livecoding';
  }, [language, pathname]);

  return null;
}

function App() {
  const theme = useThemeStore((state) => state.theme);
  const language = useLanguageStore((state) => state.language);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme === 'studio' ? 'light' : 'dark';
  }, [theme]);

  useEffect(() => { document.documentElement.lang = language; }, [language]);

  return (
    <BrowserRouter>
      <PageTitle />
      <AppRoutes />
    </BrowserRouter>
  );
}

export default App;
