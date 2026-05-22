import type { MouseEvent } from 'react';
import { File, Folder, Link } from 'lucide-react';
import type { FileEntry, ViewMode } from '../types';

interface FileAreaProps {
  entries: FileEntry[];
  selected: string[];
  viewMode: ViewMode;
  onOpen: (entry: FileEntry) => void;
  onSelect: (entry: FileEntry, event: MouseEvent<HTMLButtonElement>) => void;
  onContext: (entry: FileEntry, x: number, y: number) => void;
  onMove: (sources: string[], targetDir: string) => void;
}

function iconFor(entry: FileEntry) {
  if (entry.kind === 'directory') return <Folder size={38} />;
  if (entry.kind === 'symlink') return <Link size={34} />;
  return <File size={34} />;
}

export function FileArea({ entries, selected, viewMode, onOpen, onSelect, onContext, onMove }: FileAreaProps) {
  return (
    <section className={viewMode === 'icon' ? 'file-area icon-view' : 'file-area list-view'}>
      {entries.map((entry) => (
        <button
          key={entry.path}
          className={selected.includes(entry.path) ? 'file-item selected' : 'file-item'}
          draggable
          onDragStart={(event) => event.dataTransfer.setData('text/plain', JSON.stringify(selected.includes(entry.path) ? selected : [entry.path]))}
          onDragOver={(event) => { if (entry.kind === 'directory') event.preventDefault(); }}
          onDrop={(event) => {
            event.preventDefault();
            const sources = JSON.parse(event.dataTransfer.getData('text/plain')) as string[];
            if (entry.kind === 'directory') onMove(sources, entry.path);
          }}
          onClick={(event) => onSelect(entry, event)}
          onDoubleClick={() => onOpen(entry)}
          onContextMenu={(event) => { event.preventDefault(); onContext(entry, event.clientX, event.clientY); }}
        >
          <span className="file-icon">{iconFor(entry)}</span>
          <span className="file-name">{entry.name}</span>
          {viewMode === 'list' && <span className="file-meta">{entry.kind}</span>}
        </button>
      ))}
    </section>
  );
}
