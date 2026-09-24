declare module 'y-codemirror.next' {
  import type { Extension } from '@codemirror/state';
  import type { Awareness } from 'y-protocols/awareness';
  import type * as Y from 'yjs';

  export function yCollab(
    ytext: Y.Text,
    awareness?: Awareness | null,
    options?: { undoManager?: Y.UndoManager }
  ): Extension;
}
