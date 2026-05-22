import type { ReactNode } from 'react';
import { Clock, Folder, HardDrive, Star } from 'lucide-react';

interface SidebarProps {
  favorites: string[];
  recent: string[];
  currentPath: string;
  onNavigate: (path: string) => void;
}

export function Sidebar({ favorites, recent, currentPath, onNavigate }: SidebarProps) {
  const item = (path: string, label: string, icon: ReactNode) => (
    <button className={currentPath === path ? 'sidebar-item active' : 'sidebar-item'} onClick={() => onNavigate(path)}>
      {icon}
      <span>{label}</span>
    </button>
  );

  return (
    <aside className="sidebar">
      <h3>Locations</h3>
      {item('/', 'Files', <HardDrive size={16} />)}
      <h3>Favorites</h3>
      {favorites.length === 0 ? <p className="muted">No favorites</p> : favorites.map((path) => item(path, path.split('/').pop() || '/', <Star size={16} />))}
      <h3>Recent</h3>
      {recent.length === 0 ? <p className="muted">No recent paths</p> : recent.map((path) => item(path, path.split('/').pop() || '/', <Clock size={16} />))}
      <div className="sidebar-footer"><Folder size={15} /> Single-user mode</div>
    </aside>
  );
}
