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
    <div className="space-y-8">
      <h1 className="text-3xl font-light tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400 border-b border-white/10 pb-4">Storage Explorer</h1>
      <div className="p-8 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl">
        <h2 className="text-xl font-light text-white mb-6 uppercase tracking-widest">Top Directories</h2>
        <ul className="space-y-3">
          {data.directories.map((dir, i) => (
            <li key={i} className="flex justify-between items-center p-4 rounded-xl border border-white/5 hover:border-indigo-500/30 hover:bg-white/5 hover:-translate-y-0.5 transition-all duration-300">
              <span className="font-mono text-sm text-gray-300">{dir.top_dir}</span>
              <span className="font-light text-lg text-indigo-300 tabular-nums drop-shadow-[0_0_8px_rgba(99,102,241,0.4)]">{formatBytes(dir.total_size)}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
