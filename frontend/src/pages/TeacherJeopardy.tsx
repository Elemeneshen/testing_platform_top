import React from 'react';
import { useTranslation } from '../store/languageStore';
import './TeacherJeopardy.css';

const topics = [
  ['Алгоритмы сортировок', 'Sorting algorithms'],
  ['Процессы и потоки', 'Processes and threads'],
  ['Внутренние методы Python', 'Python internals'],
  ['Файловая система Windows', 'Windows file system'],
  ['Сокеты', 'Sockets'],
] as const;

const scores = [100, 200, 300, 400, 500] as const;

const TeacherJeopardy: React.FC = () => {
  const { t } = useTranslation();

  return <div className="jeopardy-page">
    <div className="page-heading jeopardy-page__heading">
      <div className="page-heading__copy">
        <span className="eyebrow">{t('Интерактивный зачёт', 'Interactive assessment')}</span>
        <h2>{t('Своя игра', 'Jeopardy game')}</h2>
        <p className="page-subtitle">{t('Игровое поле для командного зачёта. Вопросы и правила раунда добавим следующим этапом.', 'A game board for team assessment. Questions and round rules will be added next.')}</p>
      </div>
      <div className="jeopardy-page__status" aria-label={t('Состояние игрового поля', 'Board status')}>
        <span>{t('Черновик', 'Draft')}</span>
        <b>5 × 5</b>
      </div>
    </div>

    <section className="jeopardy-board panel" aria-label={t('Игровое поле пять на пять', 'Five by five game board')}>
      <header className="jeopardy-board__header">
        <span>{t('Тема', 'Topic')}</span>
        {scores.map((score) => <span key={score}>{score}</span>)}
      </header>

      <div className="jeopardy-board__body">
        {topics.map(([ru, en], topicIndex) => <div className="jeopardy-board__row" key={ru}>
          <div className="jeopardy-board__topic"><span>{String(topicIndex + 1).padStart(2, '0')}</span><b>{t(ru, en)}</b></div>
          {scores.map((score) => <button
            className="jeopardy-cell"
            type="button"
            key={score}
            disabled
            aria-label={t(`${ru}, ${score} баллов — вопрос пока не добавлен`, `${en}, ${score} points — no question yet`)}
          ><b>{score}</b><small>{t('Вопрос не добавлен', 'No question yet')}</small></button>)}
        </div>)}
      </div>
    </section>

    <div className="jeopardy-page__note"><span>25</span><p><b>{t('Игровых позиций подготовлено', 'Game positions prepared')}</b>{t('На следующем шаге добавим вопросы, ответы, команды и подсчёт очков.', 'Next, we can add questions, answers, teams and scoring.')}</p></div>
  </div>;
};

export default TeacherJeopardy;
