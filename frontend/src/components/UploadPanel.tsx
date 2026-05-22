interface UploadPanelProps {
  visible: boolean;
  onUpload: (file: File) => void;
  onClose: () => void;
}

export function UploadPanel({ visible, onUpload, onClose }: UploadPanelProps) {
  if (!visible) return null;
  return <div className="modal"><div className="sheet"><h2>Upload</h2><input type="file" onChange={(event) => { const file = event.target.files?.[0]; if (file) onUpload(file); }} /><button onClick={onClose}>Close</button></div></div>;
}
