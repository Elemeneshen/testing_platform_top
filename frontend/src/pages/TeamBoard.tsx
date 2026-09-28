import React, { useEffect, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useTranslation } from '../store/languageStore';
import { apiFetch } from '../utils/api';
import './TeamBoard.css';
import './TeamBoardHeader.css';
import './TeamBoardAuthor.css';

type Member = { id: number; full_name: string; username?: string };
type Team = { id: number; name: string; members: Member[] };
type Session = { id: number; group_name: string; title: string; teams: Team[] };
type Card = { id: number; column_id: number; title: string; description?: string; assignee_id?: number; created_by_student_id?: number; created_by_name?: string; priority: 'low' | 'normal' | 'high'; position: number };
type Board = { id: number; team_id: number; team_name: string; session_title: string; members: Member[]; columns: Array<{ id: number; title: string; position: number; cards: Card[] }> };

const TeamBoard: React.FC = () => {
  const navigate = useNavigate();
  const { teamId } = useParams<{ teamId: string }>();
  const role = useAuthStore((state) => state.role);
  const { t } = useTranslation();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [board, setBoard] = useState<Board | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newCards, setNewCards] = useState<Record<number, string>>({});
  const numericTeamId = Number(teamId);
  const currentSession = useMemo(() => sessions.find((session) => session.teams.some((team) => team.id === numericTeamId)), [sessions, numericTeamId]);
  const boardPath = (id: number) => role === 'teacher' ? `/teacher/teams/${id}` : `/student/teams/${id}`;

  const loadBoard = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      setBoard(await apiFetch(`/teams/${numericTeamId}/board`));
    } catch (err: any) { setError(err.message || t('Не удалось загрузить доску', 'Failed to load board')); }
    finally { if (!silent) setLoading(false); }
  };

  useEffect(() => {
    apiFetch('/teams/sessions').then(setSessions).catch(() => setSessions([]));
    loadBoard();
    const timer = window.setInterval(() => loadBoard(true), 3000);
    return () => window.clearInterval(timer);
  }, [numericTeamId]);

  const createCard = async (columnId: number) => {
    const title = newCards[columnId]?.trim(); if (!title) return;
    if (title.length > 160) { setError(t('Название карточки не должно превышать 160 символов.', 'Card title must not exceed 160 characters.')); return; }
    try {
      await apiFetch(`/teams/${numericTeamId}/cards`, { method: 'POST', body: JSON.stringify({ column_id: columnId, title }) });
      setNewCards((current) => ({ ...current, [columnId]: '' })); await loadBoard(true);
    } catch (err: any) { setError(err.message); }
  };

  const updateCard = async (cardId: number, changes: Record<string, unknown>) => {
    try { await apiFetch(`/teams/${numericTeamId}/cards/${cardId}`, { method: 'PATCH', body: JSON.stringify(changes) }); await loadBoard(true); }
    catch (err: any) { setError(err.message); }
  };

  if (loading) return <div className="loading-state">{t('Загружаем доску…', 'Loading board…')}</div>;
  if (!board) return <div className="error">{error || t('Доска не найдена', 'Board not found')}</div>;

  const appHeader = document.querySelector('.app-header');

  return <div className="team-board-page">
    {appHeader && createPortal(<div className="team-board-header-context" aria-label={t('Текущая команда', 'Current team')}><strong>{board.team_name}</strong><span>{board.members.length} {t('участников', 'members')}</span></div>, appHeader)}
    {error && <div className="error">{error}<button type="button" onClick={() => setError(null)}>×</button></div>}

    <section className="kanban-board" aria-label={t('Командная Kanban-доска', 'Team Kanban board')}>
      {board.columns.map((column) => <article className="kanban-column" key={column.id} onDragOver={(event) => event.preventDefault()} onDrop={(event) => { const cardId = Number(event.dataTransfer.getData('text/card-id')); if (cardId) updateCard(cardId, { column_id: column.id, position: column.cards.length }); }}>
        <header><h3>{column.title}</h3><span>{column.cards.length}</span></header>
        <div className="kanban-column__cards">{column.cards.map((card) => <div className={`kanban-card kanban-card--${card.priority}`} key={card.id} draggable onDragStart={(event) => event.dataTransfer.setData('text/card-id', String(card.id))}>
          <div className="kanban-card__copy"><b>{card.title}</b>{card.created_by_name && <span className="kanban-card__author">{t('Предложил', 'Suggested by')}: {card.created_by_name}</span>}{card.description && <p>{card.description}</p>}</div>
          <div className="kanban-card__controls"><label><span>{t('Приоритет', 'Priority')}</span><select value={card.priority} onChange={(event) => updateCard(card.id, { priority: event.target.value })}><option value="low">{t('Низкий', 'Low')}</option><option value="normal">{t('Обычный', 'Normal')}</option><option value="high">{t('Высокий', 'High')}</option></select></label><label><span>{t('Ответственный', 'Assignee')}</span><select value={card.assignee_id ?? ''} onChange={(event) => updateCard(card.id, { assignee_id: event.target.value ? Number(event.target.value) : null })}><option value="">{t('Не назначен', 'Unassigned')}</option>{board.members.map((member) => <option value={member.id} key={member.id}>{member.full_name}</option>)}</select></label></div>
        </div>)}</div>
        <div className="kanban-column__composer"><input maxLength={160} value={newCards[column.id] ?? ''} onChange={(event) => setNewCards({ ...newCards, [column.id]: event.target.value })} placeholder={t('Новая карточка · до 160 символов', 'New card · up to 160 characters')} onKeyDown={(event) => { if (event.key === 'Enter') createCard(column.id); }} /><button type="button" onClick={() => createCard(column.id)}>＋</button></div>
      </article>)}
    </section>

    {currentSession && currentSession.teams.length > 0 && <aside className="team-switcher" aria-label={t('Переключить команду', 'Switch team')}><span className="team-switcher__label">{t('Команды', 'Teams')}</span><div className="team-switcher__list">{currentSession.teams.map((team) => { const active = team.id === numericTeamId; return <button type="button" key={team.id} className={active ? 'team-switcher__item team-switcher__item--active' : 'team-switcher__item'} onClick={() => navigate(boardPath(team.id))} aria-current={active ? 'true' : undefined} aria-label={t(`Открыть команду ${team.name}`, `Open team ${team.name}`)}><span>{team.name.slice(0, 1).toUpperCase()}</span><b className="team-switcher__tooltip"><strong>{team.name}</strong><small>{team.members.map((member) => member.full_name).join(', ') || t('Нет участников', 'No members')}</small></b></button>; })}</div></aside>}
  </div>;
};

export default TeamBoard;
