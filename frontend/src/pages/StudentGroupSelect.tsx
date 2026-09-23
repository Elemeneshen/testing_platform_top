import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from '../utils/api';

interface Group { id: number; name: string; teacher_email?: string; student_count: number }

const StudentGroupSelect: React.FC = () => {
  const navigate = useNavigate();
  const [groups, setGroups] = useState<Group[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [currentGroup, setCurrentGroup] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([apiFetch('/student/groups'), apiFetch('/student/profile')])
      .then(([available, profile]) => { if (profile.group_id) { navigate('/test', { replace: true }); return; } setGroups(available); })
      .catch((err) => setError(err.message || 'Failed to load groups'))
      .finally(() => setLoading(false));
  }, [navigate]);

  const save = async () => {
    if (!selected) return;
    try {
      const profile = await apiFetch('/student/profile/group', { method: 'PUT', body: JSON.stringify({ group_id: selected }) });
      setCurrentGroup(profile.group_name);
      navigate('/test', { replace: true });
    } catch (err: any) { setError(err.message || 'Failed to select group'); }
  };

  if (loading) return <div className="loading-state">Loading groups…</div>;
  return <div className="group-select-page"><div className="page-heading"><div className="page-heading__copy"><span className="eyebrow">Student onboarding</span><h2>Choose your group</h2><p className="page-subtitle">This choice is confirmed once. Ask your teacher if you need to move to another group.</p></div></div>{error && <div className="error">{error}</div>}{currentGroup && <div className="success">Joining {currentGroup}…</div>}
    {groups.length === 0 ? <div className="empty-state"><span className="empty-state__icon">0</span><b>No groups available</b><p>Ask your teacher to create a group first.</p></div> : <><div className="group-choice-grid">{groups.map((group) => <button key={group.id} type="button" className={selected === group.id ? 'group-choice group-choice--selected' : 'group-choice'} onClick={() => setSelected(group.id)}><span>{group.name.slice(0, 2).toUpperCase()}</span><div><b>{group.name}</b><small>{group.teacher_email} · {group.student_count} students</small></div></button>)}</div><div className="form-actions"><button className="button" onClick={save} disabled={!selected}>{currentGroup ? 'Update group' : 'Join group'}</button></div></>}
  </div>;
};

export default StudentGroupSelect;
