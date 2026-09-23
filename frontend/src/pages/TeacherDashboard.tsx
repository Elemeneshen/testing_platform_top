import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { apiFetch } from '../utils/api';
import './TeacherDashboard.css';

const TeacherDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { role } = useAuthStore();
  const [tests, setTests] = useState<any[]>([]);
  const [groups, setGroups] = useState<any[]>([]);
  const [students, setStudents] = useState<any[]>([]);
  const [newGroupName, setNewGroupName] = useState('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const totalTasks = tests.length;

  useEffect(() => {
    // Ensure the user is a teacher
    if (role !== 'teacher') {
      navigate('/teacher/login', { replace: true });
      return;
    }

    const fetchTests = async () => {
      try {
        setLoading(true);
        setError(null);
        const [testsData, groupsData, studentsData] = await Promise.all([apiFetch('/admin/tasks'), apiFetch('/admin/groups'), apiFetch('/admin/students')]);
        setTests(testsData);
        setGroups(groupsData);
        setStudents(studentsData);
      } catch (err: any) {
        setError(err.message || 'Failed to load tests');
      } finally {
        setLoading(false);
      }
    };

    fetchTests();
  }, [navigate, role]);

  const refreshGroups = async () => setGroups(await apiFetch('/admin/groups'));
  const createGroup = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!newGroupName.trim()) return;
    try { await apiFetch('/admin/groups', { method: 'POST', body: JSON.stringify({ name: newGroupName }) }); setNewGroupName(''); await refreshGroups(); }
    catch (err: any) { setError(err.message || 'Failed to create group'); }
  };
  const renameGroup = async (group: any) => {
    const name = window.prompt('New group name', group.name)?.trim();
    if (!name || name === group.name) return;
    try { await apiFetch(`/admin/groups/${group.id}`, { method: 'PATCH', body: JSON.stringify({ name }) }); await refreshGroups(); }
    catch (err: any) { setError(err.message || 'Failed to rename group'); }
  };
  const deleteGroup = async (group: any) => {
    if (!window.confirm(`Delete group “${group.name}”?`)) return;
    try { await apiFetch(`/admin/groups/${group.id}`, { method: 'DELETE' }); await refreshGroups(); }
    catch (err: any) { setError(err.message || 'Failed to delete group'); }
  };
  const toggleTaskVisibility = async (task: any) => {
    try {
      await apiFetch(`/admin/tasks/${task.id}/visibility`, { method: 'PATCH', body: JSON.stringify({ is_visible: !task.is_visible }) });
      setTests((current) => current.map((item) => item.id === task.id ? { ...item, is_visible: !item.is_visible } : item));
    } catch (err: any) { setError(err.message || 'Failed to update visibility'); }
  };
  const changeStudentGroup = async (studentId: number, groupId: number) => {
    try {
      const profile = await apiFetch(`/admin/students/${studentId}/group`, { method: 'PATCH', body: JSON.stringify({ group_id: groupId }) });
      setStudents((current) => current.map((student) => student.id === studentId ? { ...student, group_id: profile.group_id, group_name: profile.group_name } : student));
      await refreshGroups();
    } catch (err: any) { setError(err.message || 'Failed to change student group'); }
  };

  if (loading) return <div className="loading-state">Loading workspace…</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="teacher-dashboard">
      <div className="page-heading">
        <div className="page-heading__copy"><span className="eyebrow">Teacher workspace</span><h2>Your tasks</h2><p className="page-subtitle">Assign work to groups or individual students and control when it becomes visible.</p></div>
        <div className="page-actions"><button className="button" onClick={() => navigate('/teacher/tests/create')}>＋ Create task</button></div>
      </div>

      <div className="dashboard-stats"><div className="stat-card"><span>Total tasks</span><b>{totalTasks}</b></div><div className="stat-card"><span>Published</span><b>{tests.filter((task) => task.is_visible).length}</b></div><div className="stat-card"><span>Assigned seats</span><b>{tests.reduce((count, task) => count + (task.assigned_student_count ?? 0), 0)}</b></div></div>

      <section className="group-manager panel">
        <header><div><span className="eyebrow">Class management</span><h3>Student groups</h3></div><form onSubmit={createGroup}><input value={newGroupName} onChange={(event) => setNewGroupName(event.target.value)} placeholder="New group name" maxLength={80} /><button className="button" type="submit" disabled={!newGroupName.trim()}>＋ Add group</button></form></header>
        {groups.length === 0 ? <div className="test-group__empty">No groups yet. Create one so students can join it after registration.</div> : <><div className="group-manager__grid">{groups.map((group) => <article className="group-card" key={group.id}><span className="group-card__mark">{group.name.slice(0, 2).toUpperCase()}</span><div><b>{group.name}</b><small>{group.student_count} students</small></div><div className="group-card__actions"><button type="button" onClick={() => renameGroup(group)}>Rename</button><button type="button" className="danger-link" onClick={() => deleteGroup(group)}>Delete</button></div></article>)}</div>{students.length > 0 && <div className="student-group-editor"><span className="assignment-picker__label">Student assignments</span>{students.map((student) => <div className="student-group-editor__row" key={student.id}><div><b>{student.full_name}</b><small>@{student.username}</small></div><select value={student.group_id} onChange={(event) => changeStudentGroup(student.id, Number(event.target.value))}>{groups.map((group) => <option value={group.id} key={group.id}>{group.name}</option>)}</select></div>)}</div>}</>}
      </section>

      {tests.length === 0 ? (
        <div className="empty-state"><span className="empty-state__icon">＋</span><b>No tasks yet</b><p>Create an assignment and choose who should receive it.</p><button className="button" onClick={() => navigate('/teacher/tests/create')}>Create first task</button></div>
      ) : (
          <ul className="resource-list">{tests.map((task: any, index: number) => <li className="resource-card" key={task.id}><div className="resource-card__main"><span className="resource-card__index">{String(index + 1).padStart(2, '0')}</span><div className="resource-card__copy"><b>{task.title}</b><span>{task.type === 'code_review' ? 'Code review' : 'Auto-check'} · {task.groups.map((group: any) => group.name).join(', ') || task.students.map((student: any) => student.name).join(', ')} · {task.assigned_student_count} students</span></div></div><div className="resource-card__side"><button className={task.is_visible ? 'visibility-toggle visibility-toggle--on' : 'visibility-toggle'} onClick={() => toggleTaskVisibility(task)}>{task.is_visible ? 'Visible' : 'Hidden'}</button><button className="button-secondary" onClick={() => navigate(`/teacher/task/${task.id}`)}>Progress →</button></div></li>)}</ul>
      )}
    </div>
  );
};

export default TeacherDashboard;
