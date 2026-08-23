import { useEffect, useState } from 'react';
import { getOverview } from '../api/client';
import type { StorageSummary, Forecast } from '../types';

function formatBytes(bytes: number) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export default function Overview() {
  const [data, setData] = useState<{ summary: StorageSummary, forecast: Forecast } | null>(null);

  useEffect(() => {
    getOverview().then(setData).catch(console.error);
  }, []);

  if (!data) return <div className="p-8">Loading...</div>;

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-light tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400 border-b border-white/10 pb-4">Storage Overview</h1>
      <div className="grid grid-cols-3 gap-6">
        <div className="p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl hover:-translate-y-1 hover:bg-white/5 transition-all duration-300 shadow-lg">
          <div className="text-sm text-gray-400 uppercase tracking-widest mb-2">Total Space</div>
          <div className="text-3xl font-light text-white">{formatBytes(data.summary.total_bytes)}</div>
        </div>
        <div className="p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl hover:-translate-y-1 hover:bg-white/5 transition-all duration-300 shadow-lg">
          <div className="text-sm text-gray-400 uppercase tracking-widest mb-2">Used Space</div>
          <div className="text-3xl font-light text-white">{formatBytes(data.summary.used_bytes)}</div>
        </div>
        <div className="p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl hover:-translate-y-1 hover:bg-white/5 transition-all duration-300 shadow-lg">
          <div className="text-sm text-gray-400 uppercase tracking-widest mb-2">Free Space</div>
          <div className="text-3xl font-light text-indigo-300 drop-shadow-[0_0_10px_rgba(99,102,241,0.5)]">{formatBytes(data.summary.free_bytes)}</div>
        </div>
        <div className="p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl hover:-translate-y-1 hover:bg-white/5 transition-all duration-300 shadow-lg">
          <div className="text-sm text-gray-400 uppercase tracking-widest mb-2">Utilization</div>
          <div className="text-3xl font-light text-white">{data.summary.utilization_pct}%</div>
        </div>
        <div className="p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl hover:-translate-y-1 hover:bg-white/5 transition-all duration-300 shadow-lg">
          <div className="text-sm text-gray-400 uppercase tracking-widest mb-2">AI Recommendations</div>
          <div className="text-3xl font-light text-white">{data.summary.pending_recommendations}</div>
        </div>
        <div className="p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl hover:-translate-y-1 hover:bg-white/5 transition-all duration-300 shadow-lg relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 to-transparent"></div>
          <div className="text-sm text-gray-400 uppercase tracking-widest mb-2 relative z-10">Health Score</div>
          <div className="text-3xl font-light text-white relative z-10">{data.summary.health_score}<span className="text-xl text-gray-500">/100</span></div>
        </div>
      </div>
    </div>
  );
}
