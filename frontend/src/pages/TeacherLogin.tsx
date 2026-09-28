import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { apiFetch } from '../utils/api';
import { useTranslation } from '../store/languageStore';

interface TeacherLoginCredentials {
  email: string;
  password: string;
}

const TeacherLogin: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuthStore();
  const { t } = useTranslation();
  const [credentials, setCredentials] = useState<TeacherLoginCredentials>({
    email: '',
    password: ''
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCredentials(prev => ({
      ...prev,
      [name]: value
    }));
  };

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setLoading(true);
  setError(null);
  try {
    await apiFetch('/auth/teacher-login', {
      method: 'POST',
      body: JSON.stringify({
        email: credentials.email,
        password: credentials.password,
      }),
      headers: {
        'Content-Type': 'application/json',
      },
    });
    login('teacher');
    navigate('/teacher/dashboard');
  } catch (err: any) {
    setError(err.message || t('Не удалось войти', 'Login failed'));
  } finally {
    setLoading(false);
  }
};

  return (
    <div className="login-page">
      <span className="login-page__eyebrow">{t('Защищённый вход', 'Secure access')}</span>
      <h2>{t('Вход для учителя', 'Teacher Login')}</h2>
      <p className="page-subtitle">{t('Управляйте заданиями, проверяйте код и следите за прогрессом.', 'Manage tests, review code and track student progress.')}</p>
      {error && <div className="error">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="email">Email:</label>
          <input
            type="email"
            id="email"
            name="email"
            value={credentials.email}
            onChange={handleChange}
            required
          />
        </div>
        <div>
          <label htmlFor="password">{t('Пароль:', 'Password:')}</label>
          <input
            type="password"
            id="password"
            name="password"
            value={credentials.password}
            onChange={handleChange}
            required
          />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? t('Входим…', 'Logging in...') : t('Войти', 'Login')}
        </button>
      </form>
      <p className="login-switch">{t('Вы ученик?', 'Joining a test?')} <Link to="/login">{t('Вход для ученика', 'Student sign in')}</Link></p>
    </div>
  );
};

export default TeacherLogin;
