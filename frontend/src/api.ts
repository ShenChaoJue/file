import type { DirectoryResponse, FileEntry, UserResponse } from './types';

async function request<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const response = await fetch(input, { credentials: 'include', ...init });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ error: { message: response.statusText } }));
    throw new Error(body.error?.message ?? response.statusText);
  }
  return response.json() as Promise<T>;
}

export const api = {
  me: () => request<UserResponse>('/api/auth/me'),
  login: (username: string, password: string) => request<UserResponse>('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) }),
  list: (path: string) => request<DirectoryResponse>(`/api/files?path=${encodeURIComponent(path)}`),
  createFolder: (path: string) => request<FileEntry>('/api/files/folders', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path }) }),
  rename: (path: string, newName: string) => request<FileEntry>('/api/files/rename', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path, new_name: newName }) }),
  move: (sources: string[], targetDir: string) => request<FileEntry[]>('/api/files/move', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ sources, target_dir: targetDir }) }),
  copy: (sources: string[], targetDir: string) => request<FileEntry[]>('/api/files/copy', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ sources, target_dir: targetDir }) }),
  delete: (path: string) => request<{ status: string }>(`/api/files?path=${encodeURIComponent(path)}`, { method: 'DELETE' }),
  search: (path: string, q: string) => request<{ entries: FileEntry[] }>(`/api/files/search?path=${encodeURIComponent(path)}&q=${encodeURIComponent(q)}`),
  upload: (path: string, file: File) => { const form = new FormData(); form.append('path', path); form.append('file', file); return request<FileEntry>('/api/files/upload', { method: 'POST', body: form }); },
  favorites: () => request<Array<{ path: string }>>('/api/metadata/favorites'),
  recent: () => request<Array<{ path: string }>>('/api/metadata/recent'),
  touchRecent: (path: string) => request<{ status: string }>('/api/metadata/recent', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path }) }),
  preferences: () => request<Record<string, string>>('/api/metadata/preferences'),
  setPreference: (key: string, value: string) => request<{ status: string }>('/api/metadata/preferences', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key, value }) })
};
