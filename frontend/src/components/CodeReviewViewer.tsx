import React, { useEffect, useMemo, useRef, useState } from 'react';
import { EditorState } from '@codemirror/state';
import type { Extension } from '@codemirror/state';
import { indentOnInput, indentUnit } from '@codemirror/language';
import { EditorView, keymap } from '@codemirror/view';
import { defaultKeymap, historyKeymap, indentWithTab } from '@codemirror/commands';
import { basicSetup } from 'codemirror';
import { java } from '@codemirror/lang-java';
import { python } from '@codemirror/lang-python';
import { javascript } from '@codemirror/lang-javascript';
import { html } from '@codemirror/lang-html';
import { css } from '@codemirror/lang-css';
import { oneDark } from '@codemirror/theme-one-dark';
import { HocuspocusProvider } from '@hocuspocus/provider';
import * as Y from 'yjs';
import { yCollab } from 'y-codemirror.next';
import './CodeReviewViewer.css';

interface Comment {
  line_number: number;
  text: string;
  author_type: 'student' | 'teacher';
}

interface CodeReviewViewerProps {
  code: string;
  language: string | null;
  comments: Comment[];
  enableCommenting: boolean;
  onCommentLineChange: (lineNumber: number) => void;
  onAddComment: (lineNumber: number, text: string) => void | Promise<void>;
  readOnly?: boolean;
  onCodeChange?: (code: string) => void;
  collaboration?: {
    room: string;
    user: { name: string; color: string; colorLight: string };
    onStatus?: (status: 'connecting' | 'connected' | 'disconnected') => void;
  };
  style?: React.CSSProperties;
}

const languageLabels: Record<string, string> = { java: 'Java', python: 'Python', javascript: 'JavaScript', html: 'HTML', css: 'CSS' };
const languageExtensions: Record<string, string> = { java: 'java', python: 'py', javascript: 'js', html: 'html', css: 'css' };

const getLanguagePack = (language: string | null) => {
  switch (language) {
    case 'java': return java();
    case 'python': return python();
    case 'javascript': return javascript();
    case 'html': return html();
    case 'css': return css();
    default: return null;
  }
};

const Icon = ({ name }: { name: 'code' | 'copy' | 'check' | 'message' | 'send' | 'lock' }) => {
  const paths = {
    code: <><path d="m8 9-3 3 3 3"/><path d="m16 9 3 3-3 3"/><path d="m14 6-4 12"/></>,
    copy: <><rect width="14" height="14" x="8" y="8" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></>,
    check: <path d="m5 12 4 4L19 6"/>,
    message: <path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z"/>,
    send: <><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></>,
    lock: <><rect width="16" height="12" x="4" y="10" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></>,
  };
  return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>;
};

const CodeReviewViewer: React.FC<CodeReviewViewerProps> = ({ code, language, comments, enableCommenting, onCommentLineChange, onAddComment, readOnly = true, onCodeChange, collaboration, style }) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const viewRef = useRef<EditorView | null>(null);
  const onCodeChangeRef = useRef(onCodeChange);
  const applyingExternalCodeRef = useRef(false);
  const collaborationRef = useRef<{ document: Y.Doc; provider: HocuspocusProvider; text: Y.Text } | null>(null);
  const [selectedLine, setSelectedLine] = useState(1);
  const [draft, setDraft] = useState('');
  const [copied, setCopied] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'local' | 'connecting' | 'connected' | 'disconnected'>(collaboration ? 'connecting' : 'local');
  const [participants, setParticipants] = useState(collaboration ? 1 : 0);
  onCodeChangeRef.current = onCodeChange;

  const lineCount = useMemo(() => Math.max(1, code.split('\n').length), [code]);
  const fileName = `solution.${languageExtensions[language ?? ''] ?? 'txt'}`;
  const commentCountLabel = `${comments.length} ${comments.length === 1 ? 'comment' : 'comments'}`;

  const buildExtensions = (): Extension[] => {
    const extensions: Extension[] = [basicSetup, oneDark, indentUnit.of('  '), indentOnInput(), keymap.of([...defaultKeymap, ...historyKeymap, indentWithTab]), EditorView.lineWrapping,
      EditorView.theme({ '&': { height: '100%' }, '.cm-scroller': { overflow: 'auto' }, '.cm-content': { padding: '18px 0 48px' }, '.cm-gutters': { paddingTop: '18px' } }),
      EditorView.updateListener.of((update) => {
        if (update.docChanged && !applyingExternalCodeRef.current) {
          onCodeChangeRef.current?.(update.state.doc.toString());
        }
      }),
    ];
    const languagePack = getLanguagePack(language);
    if (languagePack) extensions.push(languagePack);
    const shared = collaborationRef.current;
    if (shared?.provider.awareness) extensions.push(yCollab(shared.text, shared.provider.awareness));
    if (readOnly) extensions.push(EditorState.readOnly.of(true));
    return extensions;
  };

  useEffect(() => {
    if (!containerRef.current) return;
    let initialCode = code;
    if (collaboration) {
      const document = new Y.Doc();
      const websocketProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const provider = new HocuspocusProvider({
        url: `${websocketProtocol}//${window.location.host}/collab`,
        name: collaboration.room,
        document,
        flushDelay: 40,
        onStatus: ({ status }) => {
          setConnectionStatus(status);
          collaboration.onStatus?.(status);
        },
        onAwarenessChange: ({ states }) => setParticipants(states.length),
        onAuthenticationFailed: () => {
          setConnectionStatus('disconnected');
          collaboration.onStatus?.('disconnected');
        },
      });
      provider.setAwarenessField('user', collaboration.user);
      const text = document.getText('code');
      collaborationRef.current = { document, provider, text };
      initialCode = text.toString();
    }
    const view = new EditorView({ state: EditorState.create({ doc: initialCode, extensions: buildExtensions() }), parent: containerRef.current });
    viewRef.current = view;
    return () => {
      view.destroy();
      viewRef.current = null;
      collaborationRef.current?.provider.destroy();
      collaborationRef.current?.document.destroy();
      collaborationRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (collaborationRef.current) return;
    const view = viewRef.current;
    if (!view) return;
    view.setState(EditorState.create({ doc: view.state.doc, extensions: buildExtensions() }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [language, readOnly]);

  useEffect(() => {
    // In collaborative mode Y.Text is the only source of truth. Applying the
    // periodically fetched source_code as a CodeMirror transaction would send
    // it back to Yjs as a concurrent edit and can duplicate the document.
    if (collaborationRef.current) return;
    const view = viewRef.current;
    if (!view) return;
    const currentCode = view.state.doc.toString();
    if (currentCode !== code) {
      applyingExternalCodeRef.current = true;
      try {
        view.dispatch({ changes: { from: 0, to: currentCode.length, insert: code } });
      } finally {
        applyingExternalCodeRef.current = false;
      }
    }
  }, [code]);

  const selectLine = (lineNumber: number) => {
    const view = viewRef.current;
    if (!view) return;
    const safeLine = Math.min(Math.max(lineNumber, 1), view.state.doc.lines);
    const line = view.state.doc.line(safeLine);
    setSelectedLine(safeLine);
    onCommentLineChange(safeLine);
    view.dispatch({ selection: { anchor: line.from }, scrollIntoView: true });
  };

  const handleEditorClick = (event: React.MouseEvent) => {
    if (!enableCommenting || !viewRef.current || !(event.target as HTMLElement).closest('.cm-gutters')) return;
    const position = viewRef.current.posAtCoords({ x: event.clientX, y: event.clientY });
    if (position !== null) selectLine(viewRef.current.state.doc.lineAt(position).number);
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(viewRef.current?.state.doc.toString() ?? code);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  };

  const handleSubmitComment = async () => {
    const text = draft.trim();
    if (!text || submitting) return;
    setSubmitting(true);
    try { await onAddComment(selectedLine, text); setDraft(''); } finally { setSubmitting(false); }
  };

  return (
    <section className="live-code" style={style} aria-label="Live code review">
      <header className="live-code__topbar">
        <div className="live-code__brand"><span className="live-code__logo"><Icon name="code" /></span><span>Livecoding</span><span className={`live-code__status live-code__status--${connectionStatus}`}><i />{connectionStatus === 'connected' ? `Live · ${participants} online` : connectionStatus === 'connecting' ? 'Connecting…' : connectionStatus === 'disconnected' ? 'Offline' : 'Local session'}</span></div>
        <div className="live-code__actions"><span className="live-code__language">{languageLabels[language ?? ''] ?? 'Plain text'}</span><button type="button" className="live-code__icon-button" onClick={handleCopy} title="Copy code"><Icon name={copied ? 'check' : 'copy'} /><span>{copied ? 'Copied' : 'Copy'}</span></button></div>
      </header>

      <div className="live-code__workspace">
        <div className="live-code__editor-pane">
          <div className="live-code__tabs"><div className="live-code__tab"><span className={`live-code__file-dot live-code__file-dot--${language ?? 'text'}`} />{fileName}<span className="live-code__tab-close">×</span></div><span className="live-code__mode"><Icon name={readOnly ? 'lock' : 'code'} />{readOnly ? 'Review mode' : 'Editing'}</span></div>
          <div className="live-code__editor" ref={containerRef} onMouseDown={handleEditorClick} />
          <footer className="live-code__statusbar"><span>Ln {selectedLine}, Col 1</span><span>Spaces: 2</span><span>UTF-8</span><span>{languageLabels[language ?? ''] ?? 'Text'}</span><span>{lineCount} lines</span></footer>
        </div>

        <aside className="live-code__review">
          <div className="live-code__review-header"><div><span className="live-code__eyebrow">CODE REVIEW</span><h3>Discussion</h3></div><span className="live-code__count">{commentCountLabel}</span></div>
          <div className="live-code__comments">
            {comments.map((comment, index) => <button type="button" className="live-code__comment" key={`${comment.line_number}-${comment.text}-${index}`} onClick={() => selectLine(comment.line_number)}><span className={`live-code__avatar live-code__avatar--${comment.author_type}`}>{comment.author_type === 'teacher' ? 'T' : 'S'}</span><span className="live-code__comment-body"><span className="live-code__comment-meta"><b>{comment.author_type === 'teacher' ? 'Teacher' : 'Student'}</b><em>Line {comment.line_number}</em></span><span className="live-code__comment-text">{comment.text}</span></span></button>)}
            {comments.length === 0 && <div className="live-code__empty"><span><Icon name="message" /></span><b>No comments yet</b><p>Select a line number to start the review.</p></div>}
          </div>
          {enableCommenting && <div className="live-code__composer"><div className="live-code__composer-label"><span>Add a comment</span><button type="button" onClick={() => selectLine(selectedLine)}>Line {selectedLine}</button></div><textarea value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Share feedback or ask a question…" rows={3} onKeyDown={(event) => { if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') handleSubmitComment(); }} /><div className="live-code__composer-footer"><span>Ctrl ↵ to send</span><button type="button" onClick={handleSubmitComment} disabled={!draft.trim() || submitting}><Icon name="send" />{submitting ? 'Sending…' : 'Comment'}</button></div></div>}
        </aside>
      </div>
    </section>
  );
};

export default CodeReviewViewer;
