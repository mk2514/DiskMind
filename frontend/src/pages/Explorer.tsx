import { useEffect, useState } from 'react';
import { getDirectoryTree } from '../api/client';
import type { DirectoryInfo, FileTypeBreakdown } from '../types';

function formatBytes(bytes: number) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export default function Explorer() {
  const [data, setData] = useState<{ directories: DirectoryInfo[], file_types: FileTypeBreakdown[] } | null>(null);

  useEffect(() => {
    getDirectoryTree().then(setData).catch(console.error);
  }, []);

  if (!data) return <div className="p-8">Loading...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-black border-b border-surface-600 pb-2">Storage Explorer</h1>
      <div className="p-6 bg-surface-800 border border-surface-600">
        <h2 className="text-lg font-bold mb-4">Top Directories</h2>
        <ul className="space-y-2">
          {data.directories.map((dir, i) => (
            <li key={i} className="flex justify-between items-center p-3 border border-surface-600 hover:bg-surface-700 transition-colors">
              <span className="font-mono text-sm">{dir.top_dir}</span>
              <span className="font-bold tabular-nums">{formatBytes(dir.total_size)}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
