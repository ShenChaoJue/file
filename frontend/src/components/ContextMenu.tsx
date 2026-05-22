interface ContextMenuProps {
  x: number;
  y: number;
  visible: boolean;
  selectionCount: number;
  onClose: () => void;
  onOpen: () => void;
  onDownload: () => void;
  onRename: () => void;
  onCopy: () => void;
  onDelete: () => void;
  onDetails: () => void;
}

export function ContextMenu(props: ContextMenuProps) {
  if (!props.visible) return null;
  const action = (label: string, fn: () => void) => <button onClick={() => { fn(); props.onClose(); }}>{label}</button>;
  return (
    <div className="context-menu" style={{ left: props.x, top: props.y }}>
      {action('Open / Download', props.onOpen)}
      {action('Download', props.onDownload)}
      {props.selectionCount === 1 && action('Rename', props.onRename)}
      {action('Copy to Current Folder', props.onCopy)}
      {action('Delete', props.onDelete)}
      {props.selectionCount === 1 && action('Show Details', props.onDetails)}
    </div>
  );
}
