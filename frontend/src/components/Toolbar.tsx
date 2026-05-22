import { ChevronLeft, ChevronRight, FolderPlus, Grid2X2, List, Search, Upload } from 'lucide-react';
import type { ViewMode } from '../types';

interface ToolbarProps {
  path: string;
  viewMode: ViewMode;
  query: string;
  canBack: boolean;
  canForward: boolean;
  onBack: () => void;
  onForward: () => void;
  onQuery: (value: string) => void;
  onNewFolder: () => void;
  onUploadClick: () => void;
  onViewMode: (mode: ViewMode) => void;
}

export function Toolbar(props: ToolbarProps) {
  return (
    <header className="toolbar">
      <div className="nav-buttons">
        <button disabled={!props.canBack} onClick={props.onBack}><ChevronLeft size={18} /></button>
        <button disabled={!props.canForward} onClick={props.onForward}><ChevronRight size={18} /></button>
      </div>
      <div className="path-pill">{props.path}</div>
      <label className="search-box"><Search size={16} /><input value={props.query} onChange={(event) => props.onQuery(event.target.value)} placeholder="Search current folder" /></label>
      <button onClick={props.onNewFolder}><FolderPlus size={17} /> New Folder</button>
      <button onClick={props.onUploadClick}><Upload size={17} /> Upload</button>
      <div className="segmented">
        <button className={props.viewMode === 'icon' ? 'active' : ''} onClick={() => props.onViewMode('icon')}><Grid2X2 size={16} /></button>
        <button className={props.viewMode === 'list' ? 'active' : ''} onClick={() => props.onViewMode('list')}><List size={16} /></button>
      </div>
    </header>
  );
}
