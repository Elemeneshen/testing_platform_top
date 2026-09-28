import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useTranslation } from '../store/languageStore';
import { apiFetch } from '../utils/api';
import './TeamWorkspace.css';

type Member = { id: number; full_name: string; username?: string };
type Team = { id: number; name: string; members: Member[]; board_id?: number };
type Session = { id: number; group_id: number; group_name: string; title: string; description?: string; teams: Team[] };
type AssignmentGroup = { id: number; name: string; students: Member[] };

const TeamWorkspace: React.FC = () => {
  const navigate = useNavigate();
  const role = useAuthStore((state) => state.role);
  const { t } = useTranslation();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [groups, setGroups] = useState<AssignmentGroup[]>([]);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sessionForm, setSessionForm] = useState({ group_id: '', title: '', description: '' });
  const [teamName, setTeamName] = useState('');
  const [memberIds, setMemberIds] = useState<number[]>([]);
  const [editingTeamId, setEditingTeamId] = useState<number | null>(null);
  const [editingMemberIds, setEditingMemberIds] = useState<number[]>([]);
  const [savingMembers, setSavingMembers] = useState(false);

  const selectedSession = sessions.find((item) => item.id === sessionId) ?? sessions[0];
  const selectedGroup = groups.find((item) => item.id === selectedSession?.group_id);
  const usedMemberIds = useMemo(() => new Set(selectedSession?.teams.flatMap((team) => team.members.map((member) => member.id)) ?? []), [selectedSession]);
  const boardPath = (teamId: number) => role === 'teacher' ? `/teacher/teams/${teamId}` : `/student/teams/${teamId}`;

  const loadSessions = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      const data: Session[] = await apiFetch('/teams/sessions');
      setSessions(data);
      setSessionId((current) => current && data.some((item) => item.id === current) ? current : data[0]?.id ?? null);
    } catch (err: any) { setError(err.message || t('Не удалось загрузить командные сессии', 'Failed to load team sessions')); }
    finally { if (!silent) setLoading(false); }
  };

  useEffect(() => {
    loadSessions();
    if (role === 'teacher') apiFetch('/admin/assignment-options').then((data) => setGroups(data.groups)).catch(() => setGroups([]));
  }, [role]);

  const createSession = async (event: React.FormEvent) => {
    event.preventDefault(); setError(null);
    try {
      const created = await apiFetch('/teams/sessions', { method: 'POST', body: JSON.stringify({ ...sessionForm, group_id: Number(sessionForm.group_id) }) });
      setSessionForm({ group_id: '', title: '', description: '' });
      await loadSessions(true); setSessionId(created.id);
    } catch (err: any) { setError(err.message); }
  };

  const createTeam = async (event: React.FormEvent) => {
    event.preventDefault(); if (!selectedSession) return;
    try {
      await apiFetch(`/teams/sessions/${selectedSession.id}/teams`, { method: 'POST', body: JSON.stringify({ name: teamName, member_ids: memberIds }) });
      setTeamName(''); setMemberIds([]); await loadSessions(true);
    } catch (err: any) { setError(err.message); }
  };

  const startEditingMembers = (team: Team) => {
    setEditingTeamId(team.id);
    setEditingMemberIds(team.members.map((member) => member.id));
    setError(null);
  };

  const saveMembers = async (event: React.FormEvent, teamId: number) => {
    event.preventDefault();
    setError(null);
    setSavingMembers(true);
    try {
      await apiFetch(`/teams/${teamId}/members`, { method: 'PATCH', body: JSON.stringify({ member_ids: editingMemberIds }) });
      await loadSessions(true);
      setEditingTeamId(null);
      setEditingMemberIds([]);
    } catch (err: any) { setError(err.message || t('Не удалось обновить состав команды', 'Failed to update team members')); }
    finally { setSavingMembers(false); }
  };

  if (loading) return <div className="loading-state">{t('Загружаем команды…', 'Loading teams…')}</div>;

  return <div className="team-management">
    <div className="page-heading"><div className="page-heading__copy"><span className="eyebrow">{t('Командная работа', 'Teamwork')}</span><h2>{role === 'teacher' ? t('Управление командами', 'Team management') : t('Мои команды', 'My teams')}</h2><p className="page-subtitle">{role === 'teacher' ? t('Создавайте практики, распределяйте учеников и открывайте доски команд.', 'Create sessions, assign students and open team boards.') : t('Выберите команду, чтобы открыть её общую доску.', 'Choose a team to open its shared board.')}</p></div></div>
    {error && <div className="error">{error}</div>}

    {role === 'teacher' && <section className="team-management__create panel"><form onSubmit={createSession}><div><span className="eyebrow">{t('Новая практика', 'New practice')}</span><h3>{t('Создать командную сессию', 'Create team session')}</h3></div><select required value={sessionForm.group_id} onChange={(e) => setSessionForm({ ...sessionForm, group_id: e.target.value })}><option value="">{t('Учебная группа', 'Class group')}</option>{groups.map((group) => <option key={group.id} value={group.id}>{group.name}</option>)}</select><input required maxLength={160} placeholder={t('Название практики', 'Session title')} value={sessionForm.title} onChange={(e) => setSessionForm({ ...sessionForm, title: e.target.value })} /><textarea rows={2} placeholder={t('Общее задание или описание', 'Shared assignment or description')} value={sessionForm.description} onChange={(e) => setSessionForm({ ...sessionForm, description: e.target.value })} /><button className="button" type="submit">{t('Создать', 'Create')}</button></form></section>}

    {sessions.length === 0 ? <div className="empty-state"><span className="empty-state__icon">0</span><b>{t('Командных сессий пока нет', 'No team sessions yet')}</b><p>{role === 'teacher' ? t('Создайте первую практику для учебной группы.', 'Create the first practice for a class group.') : t('Учитель пока не добавил вас в команду.', 'Your teacher has not added you to a team yet.')}</p></div> : <div className="team-management__layout">
      <nav className="team-session-list panel" aria-label={t('Командные сессии', 'Team sessions')}>{sessions.map((item) => <button type="button" key={item.id} className={selectedSession?.id === item.id ? 'active' : ''} onClick={() => setSessionId(item.id)}><b>{item.title}</b><small>{item.group_name} · {item.teams.length} {t('команд', 'teams')}</small></button>)}</nav>
      {selectedSession && <section className="team-management__session">
        <header className="panel"><div><span className="eyebrow">{selectedSession.group_name}</span><h3>{selectedSession.title}</h3><p>{selectedSession.description || t('Описание не добавлено.', 'No description provided.')}</p></div>
          {role === 'teacher' && <form onSubmit={createTeam}><input required maxLength={80} placeholder={t('Название команды', 'Team name')} value={teamName} onChange={(e) => setTeamName(e.target.value)} /><div className="team-member-picker">{selectedGroup?.students.map((student) => <label key={student.id} className={usedMemberIds.has(student.id) ? 'disabled' : ''}><input type="checkbox" disabled={usedMemberIds.has(student.id)} checked={memberIds.includes(student.id)} onChange={(e) => setMemberIds(e.target.checked ? [...memberIds, student.id] : memberIds.filter((id) => id !== student.id))} />{student.full_name}</label>)}</div><button className="button-secondary" type="submit">{t('＋ Добавить команду', '＋ Add team')}</button></form>}
        </header>
        {selectedSession.teams.length === 0 ? <div className="empty-state"><b>{t('Команд пока нет', 'No teams yet')}</b><p>{t('Создайте команду и выберите её участников.', 'Create a team and choose its members.')}</p></div> : <div className="team-management__teams">{selectedSession.teams.map((team) => {
          const editing = editingTeamId === team.id;
          const occupiedByOtherTeams = new Set(selectedSession.teams.filter((item) => item.id !== team.id).flatMap((item) => item.members.map((member) => member.id)));
          return <article className={editing ? 'team-entry team-entry--editing panel' : 'team-entry panel'} key={team.id}>
            <span className="team-entry__mark">{team.name.slice(0, 1).toUpperCase()}</span>
            <div className="team-entry__content"><h4>{team.name}</h4>{team.members.length > 0 ? <div className="team-entry__members">{team.members.map((member) => <span key={member.id}>{member.full_name}</span>)}</div> : <p>{t('Участники не назначены', 'No members assigned')}</p>}</div>
            <div className="team-entry__actions">{role === 'teacher' && <button className="button-ghost" type="button" onClick={() => editing ? setEditingTeamId(null) : startEditingMembers(team)}>{editing ? t('Закрыть', 'Close') : t('Состав', 'Members')}</button>}<button className="button-secondary" type="button" onClick={() => navigate(boardPath(team.id))}>{t('Открыть доску →', 'Open board →')}</button></div>
            {editing && <form className="team-member-editor" onSubmit={(event) => saveMembers(event, team.id)}>
              <div className="team-member-editor__heading"><div><b>{t('Состав команды', 'Team members')}</b><small>{editingMemberIds.length} {t('участников выбрано', 'members selected')}</small></div><button className="button" type="submit" disabled={savingMembers}>{savingMembers ? t('Сохраняем…', 'Saving…') : t('Сохранить состав', 'Save members')}</button></div>
              <div className="team-member-editor__grid">{selectedGroup?.students.map((student) => { const occupied = occupiedByOtherTeams.has(student.id); const checked = editingMemberIds.includes(student.id); return <label key={student.id} className={occupied ? 'disabled' : checked ? 'selected' : ''}><input type="checkbox" disabled={occupied} checked={checked} onChange={(event) => setEditingMemberIds(event.target.checked ? [...editingMemberIds, student.id] : editingMemberIds.filter((id) => id !== student.id))} /><span><b>{student.full_name}</b><small>{occupied ? t('Уже в другой команде', 'Already in another team') : student.username ? `@${student.username}` : t('Доступен', 'Available')}</small></span></label>; })}</div>
            </form>}
          </article>;
        })}</div>}
      </section>}
    </div>}
  </div>;
};

export default TeamWorkspace;
