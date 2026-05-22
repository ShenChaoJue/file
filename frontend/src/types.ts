export type FileKind = 'file' | 'directory' | 'symlink' | 'other';

export interface FileEntry {
  name: string;
  path: string;
  kind: FileKind;
  size: number | null;
  modified_at: string | null;
  can_download: boolean;
}

export interface DirectoryResponse {
  path: string;
  entries: FileEntry[];
}

export interface UserResponse {
  username: string;
}

export type ViewMode = 'icon' | 'list';
