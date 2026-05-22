import type { FileEntry } from '../types';

interface DialogsProps {
  renameValue: string;
  setRenameValue: (value: string) => void;
  renaming: boolean;
  details: FileEntry | null;
  confirmDelete: boolean;
  onRenameConfirm: () => void;
  onDeleteConfirm: () => void;
  onClose: () => void;
}

export function Dialogs(props: DialogsProps) {
  return (
    <>
      {props.renaming && <div className="modal"><div className="sheet"><h2>Rename</h2><input autoFocus value={props.renameValue} onChange={(event) => props.setRenameValue(event.target.value)} /><button onClick={props.onRenameConfirm}>Rename</button><button onClick={props.onClose}>Cancel</button></div></div>}
      {props.confirmDelete && <div className="modal"><div className="sheet"><h2>Move to Trash?</h2><p>This moves selected items to the app-managed trash.</p><button className="danger" onClick={props.onDeleteConfirm}>Delete</button><button onClick={props.onClose}>Cancel</button></div></div>}
      {props.details && <div className="modal"><div className="sheet"><h2>{props.details.name}</h2><p>Path: {props.details.path}</p><p>Type: {props.details.kind}</p><p>Size: {props.details.size ?? '—'}</p><p>Modified: {props.details.modified_at ?? '—'}</p><button onClick={props.onClose}>Close</button></div></div>}
    </>
  );
}
