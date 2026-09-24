import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { apiFetch } from '../utils/api';

const StudentRegister: React.FC = () => {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const [form, setForm] = useState({ full_name: '', username: '', password: '', confirm: '', registration_code: '' });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (form.password !== form.confirm) return setError('Passwords do not match');
    try {
      setLoading(true); setError(null);
      await apiFetch('/auth/student-register', { method: 'POST', body: JSON.stringify({ full_name: form.full_name, username: form.username, password: form.password, registration_code: form.registration_code.trim().toUpperCase() }) });
      login('student');
      navigate('/student/group');
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    } finally { setLoading(false); }
  };

  return <div className="login-page"><h2>Create student account</h2><p className="page-subtitle">Your account will keep your progress and code between sessions.</p>{error && <div className="error">{error}</div>}<form onSubmit={submit}>
    <div><label htmlFor="registration-code">Teacher registration code</label><input id="registration-code" value={form.registration_code} onChange={(e) => setForm({ ...form, registration_code: e.target.value.toUpperCase() })} minLength={6} maxLength={12} autoComplete="off" placeholder="Ask your teacher" required /></div>
    <div><label htmlFor="full-name">Full name</label><input id="full-name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required /></div>
    <div><label htmlFor="new-username">Username</label><input id="new-username" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} minLength={3} required /></div>
    <div><label htmlFor="new-password">Password</label><input id="new-password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} minLength={8} required /></div>
    <div><label htmlFor="confirm-password">Confirm password</label><input id="confirm-password" type="password" value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} required /></div>
    <button type="submit" disabled={loading}>{loading ? 'Creating account…' : 'Create account'}</button>
  </form><p className="login-switch">Already registered? <Link to="/login">Sign in</Link></p></div>;
};

export default StudentRegister;
