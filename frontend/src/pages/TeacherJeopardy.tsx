import React, { useEffect, useMemo, useState } from 'react';
import { useTranslation } from '../store/languageStore';
import './TeacherJeopardy.css';

type Text = { ru: string; en: string };
type Question = { topic: Text; score: number; question: Text; answer: Text };
type Player = { id: string; name: string; score: number };
type Game = { players: Player[]; used: string[] };

const topicTexts: Text[] = [
  { ru: 'Алгоритмы сортировок', en: 'Sorting algorithms' },
  { ru: 'Процессы и потоки', en: 'Processes and threads' },
  { ru: 'Внутренние методы Python', en: 'Python internals' },
  { ru: 'Файловая система Windows', en: 'Windows file system' },
  { ru: 'Сокеты', en: 'Sockets' },
];

const rawQuestions: Array<[number, number, string, string, string, string]> = [
  [0,100,'Какая сортировка сравнивает соседние элементы и меняет их местами?','Which sorting algorithm compares adjacent elements and swaps them?','Пузырьковая сортировка (Bubble Sort).','Bubble Sort.'],
  [0,200,'Какова средняя временная сложность быстрой сортировки?','What is the average time complexity of Quick Sort?','O(n log n).','O(n log n).'],
  [0,300,'Что означает стабильность алгоритма сортировки?','What does sorting algorithm stability mean?','Элементы с одинаковыми ключами сохраняют исходный взаимный порядок.','Elements with equal keys keep their original relative order.'],
  [0,400,'Почему сортировка слиянием требует дополнительную память?','Why does Merge Sort require additional memory?','Для временных массивов, в которые сливаются отсортированные части.','It needs temporary arrays to merge sorted parts.'],
  [0,500,'Назовите нижнюю границу сложности сортировки сравнениями в общем случае.','State the lower complexity bound for comparison sorting in the general case.','Ω(n log n), потому что дерево решений должно различать n! перестановок.','Ω(n log n), because the decision tree must distinguish n! permutations.'],
  [1,100,'Что имеет собственное адресное пространство: процесс или поток?','Which has its own address space: a process or a thread?','Процесс. Потоки одного процесса разделяют его память.','A process. Threads of one process share its memory.'],
  [1,200,'Как называется переключение процессора с одной задачи на другую?','What is switching the CPU from one task to another called?','Переключение контекста (context switch).','A context switch.'],
  [1,300,'Для чего нужен мьютекс?','What is a mutex used for?','Для взаимного исключения: он защищает общий ресурс от одновременного доступа.','For mutual exclusion: it protects a shared resource from concurrent access.'],
  [1,400,'Назовите четыре необходимых условия возникновения взаимной блокировки.','Name the four necessary conditions for a deadlock.','Взаимное исключение, удержание и ожидание, отсутствие принудительного освобождения, циклическое ожидание.','Mutual exclusion, hold and wait, no preemption, and circular wait.'],
  [1,500,'Чем параллелизм отличается от конкурентности?','How does parallelism differ from concurrency?','Конкурентность — задачи продвигаются вперемешку; параллелизм — реально выполняются одновременно на разных ядрах.','Concurrency interleaves progress; parallelism executes tasks simultaneously on different cores.'],
  [2,100,'Какой специальный метод вызывается функцией len(obj)?','Which special method is called by len(obj)?','__len__.','__len__.'],
  [2,200,'Какие методы позволяют объекту работать в конструкции with?','Which methods let an object work in a with statement?','__enter__ и __exit__.','__enter__ and __exit__.'],
  [2,300,'Чем __repr__ обычно отличается от __str__?','How does __repr__ usually differ from __str__?','__repr__ даёт однозначное представление для разработчика, __str__ — читаемое для пользователя.','__repr__ is an unambiguous developer representation; __str__ is user-friendly.'],
  [2,400,'Какой протокол использует цикл for и какие методы в нём участвуют?','Which protocol does a for loop use, and which methods take part?','Протокол итератора: __iter__ возвращает итератор, __next__ выдаёт значения до StopIteration.','The iterator protocol: __iter__ returns an iterator and __next__ yields values until StopIteration.'],
  [2,500,'Что происходит при обращении к obj.attribute на уровне специальных методов?','What happens at the special-method level when accessing obj.attribute?','Сначала вызывается __getattribute__; если атрибут не найден, может быть вызван __getattr__.','__getattribute__ is called first; if lookup fails, __getattr__ may be called.'],
  [3,100,'Как называется основная файловая система современных версий Windows?','What is the main file system of modern Windows versions?','NTFS.','NTFS.'],
  [3,200,'Какой символ разделяет каталоги в пути Windows?','Which character separates directories in a Windows path?','Обратная косая черта: \\.','A backslash: \\.'],
  [3,300,'Что хранит MFT в файловой системе NTFS?','What does the MFT store in NTFS?','Записи и метаданные обо всех файлах и каталогах тома.','Records and metadata for every file and directory on the volume.'],
  [3,400,'Чем абсолютный путь отличается от относительного?','How does an absolute path differ from a relative path?','Абсолютный начинается от корня или диска, относительный вычисляется от текущего рабочего каталога.','An absolute path starts at a root or drive; a relative path is resolved from the current working directory.'],
  [3,500,'Что такое ACL файла в Windows?','What is a file ACL in Windows?','Список управления доступом: набор правил, определяющих права пользователей и групп на объект.','An access control list: rules defining user and group permissions for an object.'],
  [4,100,'Какие два транспортных протокола чаще всего используются с сокетами?','Which two transport protocols are most commonly used with sockets?','TCP и UDP.','TCP and UDP.'],
  [4,200,'Из каких двух основных частей состоит сетевой адрес сокета?','What are the two main parts of a socket network address?','IP-адрес и номер порта.','An IP address and a port number.'],
  [4,300,'В каком порядке TCP-сервер обычно вызывает bind, listen и accept?','In what order does a TCP server usually call bind, listen, and accept?','bind → listen → accept.','bind → listen → accept.'],
  [4,400,'Почему один вызов recv не гарантирует получение всего TCP-сообщения?','Why does one recv call not guarantee receiving a complete TCP message?','TCP передаёт поток байтов без границ сообщений; данные могут прийти частями.','TCP is a byte stream without message boundaries, so data may arrive in chunks.'],
  [4,500,'Что происходит во время трёхэтапного рукопожатия TCP?','What happens during the TCP three-way handshake?','Клиент отправляет SYN, сервер отвечает SYN-ACK, клиент подтверждает ACK.','The client sends SYN, the server replies SYN-ACK, and the client confirms with ACK.'],
];

const questions: Question[] = rawQuestions.map(([topic, score, qr, qe, ar, ae]) => ({ topic: topicTexts[topic], score, question: { ru: qr, en: qe }, answer: { ru: ar, en: ae } }));
const scores = [100, 200, 300, 400, 500];
const storageKey = 'teacher-jeopardy-state-v1';
const keyFor = (question: Question) => `${question.topic.ru}:${question.score}`;
const loadGame = (): Game => { try { const value = JSON.parse(localStorage.getItem(storageKey) || '') as Game; return { players: Array.isArray(value.players) ? value.players : [], used: Array.isArray(value.used) ? value.used : [] }; } catch { return { players: [], used: [] }; } };

const TeacherJeopardy: React.FC = () => {
  const { t } = useTranslation();
  const [game, setGame] = useState<Game>(loadGame);
  const [playerName, setPlayerName] = useState('');
  const [active, setActive] = useState<Question | null>(null);
  const [playerId, setPlayerId] = useState<string | null>(null);
  const [answerVisible, setAnswerVisible] = useState(false);
  const activePlayer = game.players.find((player) => player.id === playerId);
  const remaining = useMemo(() => questions.length - game.used.length, [game.used]);

  useEffect(() => localStorage.setItem(storageKey, JSON.stringify(game)), [game]);
  const close = () => { setActive(null); setPlayerId(null); setAnswerVisible(false); };
  const open = (question: Question) => { setActive(question); setPlayerId(null); setAnswerVisible(false); };
  const addPlayer = (event: React.FormEvent) => { event.preventDefault(); const name = playerName.trim(); if (!name) return; setGame((value) => ({ ...value, players: [...value.players, { id: crypto.randomUUID(), name, score: 0 }] })); setPlayerName(''); };
  const applyScore = (direction: 1 | -1) => { if (!active || !playerId) return; const key = keyFor(active); setGame((value) => ({ players: value.players.map((player) => player.id === playerId ? { ...player, score: player.score + active.score * direction } : player), used: value.used.includes(key) ? value.used : [...value.used, key] })); close(); };
  const reset = () => { if (window.confirm(t('Сбросить очки и вернуть все вопросы на поле?', 'Reset scores and return every question to the board?'))) setGame((value) => ({ players: value.players.map((player) => ({ ...player, score: 0 })), used: [] })); };

  return <div className="jeopardy-page">
    <div className="page-heading jeopardy-page__heading"><div className="page-heading__copy"><span className="eyebrow">{t('Интерактивный зачёт','Interactive assessment')}</span><h2>{t('Своя игра','Jeopardy game')}</h2><p className="page-subtitle">{t('Выберите стоимость, назначьте отвечающего и переверните карточку после ответа.','Choose a value, assign a player and flip the card after their answer.')}</p></div><div className="jeopardy-page__status"><span>{t('В игре','In play')}</span><b>{remaining} / 25</b></div></div>
    <section className="jeopardy-board panel" aria-label={t('Игровое поле пять на пять','Five by five game board')}>
      <header className="jeopardy-board__header"><span>{t('Тема','Topic')}</span>{scores.map((score) => <span key={score}>{score}</span>)}</header>
      <div>{topicTexts.map((topic, topicIndex) => <div className="jeopardy-board__row" key={topic.ru}><div className="jeopardy-board__topic"><span>{String(topicIndex + 1).padStart(2,'0')}</span><b>{t(topic.ru,topic.en)}</b></div>{scores.map((score) => { const question = questions.find((item) => item.topic.ru === topic.ru && item.score === score)!; const used = game.used.includes(keyFor(question)); return <button className={`jeopardy-cell${used ? ' jeopardy-cell--used' : ''}`} type="button" key={score} onClick={() => open(question)}><b>{used ? '—' : score}</b><small>{used ? t('Сыграно','Played') : t('Открыть вопрос','Open question')}</small></button>; })}</div>)}</div>
    </section>
    <section className="jeopardy-scoreboard panel"><header><div><span className="eyebrow">{t('Табло','Scoreboard')}</span><h3>{t('Участники игры','Game players')}</h3></div><button className="jeopardy-reset" type="button" onClick={reset}>{t('Сбросить раунд','Reset round')}</button></header><form className="jeopardy-player-form" onSubmit={addPlayer}><input value={playerName} onChange={(event) => setPlayerName(event.target.value)} maxLength={60} placeholder={t('Имя ученика','Student name')} /><button type="submit" disabled={!playerName.trim()}>{t('Добавить','Add')}</button></form>
      {game.players.length ? <div className="jeopardy-players">{game.players.map((player,index) => <article className="jeopardy-player" key={player.id}><span>{String(index + 1).padStart(2,'0')}</span><div><b>{player.name}</b><small>{t('Участник','Player')}</small></div><strong>{player.score}</strong><button type="button" onClick={() => setGame((value) => ({ ...value, players: value.players.filter((item) => item.id !== player.id) }))} aria-label={t(`Удалить ${player.name}`,`Remove ${player.name}`)}>×</button></article>)}</div> : <p className="jeopardy-scoreboard__empty">{t('Добавьте учеников — они появятся здесь вместе со счётом.','Add students and their scores will appear here.')}</p>}
    </section>
    {active && <div className="jeopardy-dialog" role="dialog" aria-modal="true" onMouseDown={(event) => event.target === event.currentTarget && close()}><section className="jeopardy-dialog__panel"><header><div><span>{t(active.topic.ru,active.topic.en)}</span><b>{active.score}</b></div><button type="button" onClick={close}>×</button></header><div className={`jeopardy-flip${answerVisible ? ' jeopardy-flip--answer' : ''}`}><div className="jeopardy-flip__inner"><article className="jeopardy-flip__face"><small>{t('Вопрос','Question')}</small><h3>{t(active.question.ru,active.question.en)}</h3></article><article className="jeopardy-flip__face jeopardy-flip__back"><small>{t('Ответ','Answer')}</small><h3>{t(active.answer.ru,active.answer.en)}</h3></article></div></div>
      <div className="jeopardy-dialog__players"><span>{t('Кто отвечает?','Who is answering?')}</span>{game.players.length ? <div>{game.players.map((player) => <button className={playerId === player.id ? 'active' : ''} type="button" key={player.id} onClick={() => setPlayerId(player.id)}><b>{player.name}</b><small>{player.score}</small></button>)}</div> : <p>{t('Сначала добавьте учеников в табло под игровым полем.','Add students to the scoreboard below the board first.')}</p>}</div>
      <footer><button className="jeopardy-reveal" type="button" onClick={() => setAnswerVisible((value) => !value)}>{answerVisible ? t('Вернуть вопрос','Show question') : t('Показать ответ','Show answer')}</button><div><button type="button" disabled={!answerVisible || !activePlayer} onClick={() => applyScore(-1)}>{t(`Неверно −${active.score}`,`Incorrect −${active.score}`)}</button><button type="button" disabled={!answerVisible || !activePlayer} onClick={() => applyScore(1)}>{t(`Верно +${active.score}`,`Correct +${active.score}`)}</button></div></footer></section></div>}
  </div>;
};

export default TeacherJeopardy;
