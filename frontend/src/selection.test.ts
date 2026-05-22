import { describe, expect, it } from 'vitest';
import { rangeSelection, toggleSelection } from './selection';
describe('selection model', () => {
  it('toggles a path on and off', () => { expect(toggleSelection([], '/a.txt')).toEqual(['/a.txt']); expect(toggleSelection(['/a.txt'], '/a.txt')).toEqual([]); });
  it('selects an inclusive range between anchor and target', () => { expect(rangeSelection(['/a.txt', '/b.txt', '/c.txt', '/d.txt'], '/b.txt', '/d.txt')).toEqual(['/b.txt', '/c.txt', '/d.txt']); });
  it('falls back to target when anchor is missing', () => { expect(rangeSelection(['/a.txt'], '/missing', '/a.txt')).toEqual(['/a.txt']); });
});
