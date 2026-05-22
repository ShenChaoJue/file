export function toggleSelection(selected: string[], path: string): string[] {
  return selected.includes(path) ? selected.filter((item) => item !== path) : [...selected, path];
}

export function rangeSelection(allPaths: string[], anchor: string | null, target: string): string[] {
  const targetIndex = allPaths.indexOf(target);
  const anchorIndex = anchor ? allPaths.indexOf(anchor) : -1;
  if (targetIndex === -1) return [];
  if (anchorIndex === -1) return [target];
  const start = Math.min(anchorIndex, targetIndex);
  const end = Math.max(anchorIndex, targetIndex);
  return allPaths.slice(start, end + 1);
}
