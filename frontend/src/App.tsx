import { useEffect, useMemo, useState } from 'react';
import { api } from './api';
import { rangeSelection, toggleSelection } from './selection';
import type { FileEntry, ViewMode } from './types';
import { AppShell } from './components/AppShell';
import { Sidebar } from './components/Sidebar';
import { Toolbar } from './components/Toolbar';
import { FileArea } from './components/FileArea';
import { ContextMenu } from './components/ContextMenu';
import { Dialogs } from './components/Dialogs';
import { UploadPanel } from './components/UploadPanel';

function download(path: string) {
  window.location.href = `/api/files/download?path=${encodeURIComponent(path)}`;
}

export default function App() {
  const [user, setUser] = useState<string | null>(null);
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [path, setPath] = useState('/');
  const [entries, setEntries] = useState<FileEntry[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [anchor, setAnchor] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('icon');
  const [history, setHistory] = useState<string[]>(['/']);
  const [historyIndex, setHistoryIndex] = useState(0);
  const [query, setQuery] = useState('');
  const [favorites, setFavorites] = useState<string[]>([]);
  const [recent, setRecent] = useState<string[]>([]);
  const [menu, setMenu] = useState({ visible: false, x: 0, y: 0 });
  const [renaming, setRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState('');
  const [details, setDetails] = useState<FileEntry | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [error, setError] = useState('');

  const selectedEntries = useMemo(() => entries.filter((entry) => selected.includes(entry.path)), [entries, selected]);

  async function refresh(nextPath = path, nextQuery = query) {
    setError('');
    const data = nextQuery ? await api.search(nextPath, nextQuery) : await api.list(nextPath);
    setEntries(data.entries);
    await api.touchRecent(nextPath).catch(() => undefined);
    setRecent((await api.recent().catch(() => [])).map((item) => item.path));
  }

  async function navigate(nextPath: string, record = true) {
    setPath(nextPath);
    setSelected([]);
    setAnchor(null);
    if (record) {
      const nextHistory = history.slice(0, historyIndex + 1).concat(nextPath);
      setHistory(nextHistory);
      setHistoryIndex(nextHistory.length - 1);
    }
    await refresh(nextPath, query);
  }

  useEffect(() => { api.me().then((me) => setUser(me.username)).catch(() => undefined); }, []);
  useEffect(() => { if (user) { refresh('/').catch((exc) => setError(String(exc.message ?? exc))); api.favorites().then((items) => setFavorites(items.map((item) => item.path))).catch(() => undefined); api.preferences().then((prefs) => { if (prefs.viewMode === 'icon' || prefs.viewMode === 'list') setViewMode(prefs.viewMode); }).catch(() => undefined); } }, [user]);
  useEffect(() => { if (user) refresh(path, query).catch((exc) => setError(String(exc.message ?? exc))); }, [query]);

  if (!user) {
    return <main className="login-screen"><form onSubmit={async (event) => { event.preventDefault(); try { const me = await api.login(username, password); setUser(me.username); } catch (exc) { setError(String((exc as Error).message)); } }}><h1>Personal File Manager</h1><input value={username} onChange={(event) => setUsername(event.target.value)} /><input type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Password" /><button>Login</button>{error && <p className="error">{error}</p>}</form></main>;
  }

  const current = selectedEntries[0];
  return (
    <AppShell>
      <Sidebar favorites={favorites} recent={recent} currentPath={path} onNavigate={navigate} />
      <section className="main-pane" onClick={() => setMenu((old) => ({ ...old, visible: false }))}>
        <Toolbar path={path} viewMode={viewMode} query={query} canBack={historyIndex > 0} canForward={historyIndex < history.length - 1} onBack={() => { const i = historyIndex - 1; setHistoryIndex(i); navigate(history[i], false); }} onForward={() => { const i = historyIndex + 1; setHistoryIndex(i); navigate(history[i], false); }} onQuery={setQuery} onNewFolder={async () => { const name = prompt('Folder name'); if (name) { await api.createFolder(`${path === '/' ? '' : path}/${name}`); await refresh(); } }} onUploadClick={() => setUploadOpen(true)} onViewMode={(mode) => { setViewMode(mode); api.setPreference('viewMode', mode).catch(() => undefined); }} />
        {error && <p className="banner">{error}</p>}
        <FileArea entries={entries} selected={selected} viewMode={viewMode} onOpen={(entry) => { if (entry.kind === 'directory') navigate(entry.path); else download(entry.path); }} onSelect={(entry, event) => { const all = entries.map((item) => item.path); if (event.shiftKey) setSelected(rangeSelection(all, anchor, entry.path)); else if (event.metaKey || event.ctrlKey) setSelected(toggleSelection(selected, entry.path)); else setSelected([entry.path]); setAnchor(entry.path); }} onContext={(entry, x, y) => { if (!selected.includes(entry.path)) setSelected([entry.path]); setMenu({ visible: true, x, y }); }} onMove={async (sources, targetDir) => { await api.move(sources, targetDir); await refresh(); }} />
        <ContextMenu visible={menu.visible} x={menu.x} y={menu.y} selectionCount={selected.length} onClose={() => setMenu((old) => ({ ...old, visible: false }))} onOpen={() => current && (current.kind === 'directory' ? navigate(current.path) : download(current.path))} onDownload={() => current && download(current.path)} onRename={() => { setRenameValue(current?.name ?? ''); setRenaming(true); }} onCopy={async () => { await api.copy(selected, path); await refresh(); }} onDelete={() => setConfirmDelete(true)} onDetails={() => setDetails(current ?? null)} />
        <Dialogs renameValue={renameValue} setRenameValue={setRenameValue} renaming={renaming} details={details} confirmDelete={confirmDelete} onRenameConfirm={async () => { if (current) await api.rename(current.path, renameValue); setRenaming(false); await refresh(); }} onDeleteConfirm={async () => { for (const item of selected) await api.delete(item); setConfirmDelete(false); setSelected([]); await refresh(); }} onClose={() => { setRenaming(false); setDetails(null); setConfirmDelete(false); }} />
        <UploadPanel visible={uploadOpen} onUpload={async (file) => { await api.upload(path, file); setUploadOpen(false); await refresh(); }} onClose={() => setUploadOpen(false)} />
      </section>
    </AppShell>
  );
}
