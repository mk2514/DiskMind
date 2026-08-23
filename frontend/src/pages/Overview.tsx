import { useEffect, useState } from 'react';
import { getOverview, isDemoMode } from '../api/client';
import type { StorageSummary, Forecast } from '../types';
import { HardDrive, Database, ShieldCheck, Activity, Sparkles, HeartPulse } from 'lucide-react';
import SetupGuide from '../components/SetupGuide';

function formatBytes(bytes: number) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export default function Overview() {
  const [data, setData] = useState<{ summary: StorageSummary, forecast: Forecast } | null>(null);
  const [error, setError] = useState<string | undefined>(undefined);

  const loadData = () => {
    getOverview()
      .then((d) => {
        setData(d);
        setError(undefined);
      })
      .catch((e) => setError(e.message));
  };

  useEffect(() => {
    loadData();
    if (!isDemoMode()) {
      const interval = setInterval(loadData, 3000);
      return () => clearInterval(interval);
    }
  }, []);

  const needsSetup = !isDemoMode() && (!data || !data.summary || data.summary.total_bytes === null || data.summary.total_bytes === undefined);

  if (needsSetup) {
    return <SetupGuide error={error} />;
  }

  if (!data) return <div className="p-8 text-gray-500">Loading...</div>;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <h1 className="text-3xl font-light tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400">Storage Overview</h1>
        {!isDemoMode() && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/30 rounded-full">
            <div className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] animate-pulse"></div>
            <span className="text-xs text-emerald-300 font-medium tracking-wide uppercase">Live Connection Active</span>
          </div>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        
        {/* Total Space */}
        <div className="p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl hover:-translate-y-1 hover:bg-white/5 transition-all duration-300 shadow-lg relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-20 transition-opacity"><HardDrive size={64} /></div>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-white/10 rounded-lg"><HardDrive className="w-5 h-5 text-gray-300" /></div>
            <div className="text-sm text-gray-400 uppercase tracking-widest">Total Space</div>
          </div>
          <div className="text-4xl font-light text-white">{formatBytes(data.summary.total_bytes)}</div>
        </div>

        {/* Used Space */}
        <div className="p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl hover:-translate-y-1 hover:bg-white/5 transition-all duration-300 shadow-lg relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-20 transition-opacity"><Database size={64} /></div>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-indigo-500/20 rounded-lg"><Database className="w-5 h-5 text-indigo-400" /></div>
            <div className="text-sm text-gray-400 uppercase tracking-widest">Used Space</div>
          </div>
          <div className="text-4xl font-light text-white">{formatBytes(data.summary.used_bytes)}</div>
          <div className="mt-4 w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
            <div className="bg-indigo-500 h-full rounded-full shadow-[0_0_10px_rgba(99,102,241,0.8)]" style={{ width: `${data.summary.utilization_pct}%` }}></div>
          </div>
        </div>

        {/* Free Space */}
        <div className="p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl hover:-translate-y-1 hover:bg-white/5 transition-all duration-300 shadow-lg relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-20 transition-opacity"><ShieldCheck size={64} /></div>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-emerald-500/20 rounded-lg"><ShieldCheck className="w-5 h-5 text-emerald-400" /></div>
            <div className="text-sm text-gray-400 uppercase tracking-widest">Free Space</div>
          </div>
          <div className="text-4xl font-light text-emerald-300 drop-shadow-[0_0_10px_rgba(52,211,153,0.5)]">{formatBytes(data.summary.free_bytes)}</div>
        </div>

        {/* Utilization */}
        <div className="p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl hover:-translate-y-1 hover:bg-white/5 transition-all duration-300 shadow-lg relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-20 transition-opacity"><Activity size={64} /></div>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-rose-500/20 rounded-lg"><Activity className="w-5 h-5 text-rose-400" /></div>
            <div className="text-sm text-gray-400 uppercase tracking-widest">Utilization</div>
          </div>
          <div className="flex items-end gap-2">
            <div className="text-4xl font-light text-white">{data.summary.utilization_pct}</div>
            <div className="text-xl text-gray-500 mb-1">%</div>
          </div>
        </div>

        {/* AI Recommendations */}
        <div className="p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl hover:-translate-y-1 hover:bg-white/5 transition-all duration-300 shadow-lg relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-20 transition-opacity"><Sparkles size={64} /></div>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-amber-500/20 rounded-lg"><Sparkles className="w-5 h-5 text-amber-400" /></div>
            <div className="text-sm text-gray-400 uppercase tracking-widest">AI Insights</div>
          </div>
          <div className="flex items-end gap-2">
            <div className="text-4xl font-light text-amber-300 drop-shadow-[0_0_10px_rgba(251,191,36,0.4)]">{data.summary.pending_recommendations}</div>
            <div className="text-sm text-gray-500 mb-1.5 uppercase tracking-wide">Actions</div>
          </div>
        </div>

        {/* Health Score */}
        <div className="p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl hover:-translate-y-1 hover:bg-white/5 transition-all duration-300 shadow-lg relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-transparent"></div>
          <div className="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-20 transition-opacity"><HeartPulse size={64} /></div>
          <div className="flex items-center gap-3 mb-4 relative z-10">
            <div className="p-2 bg-cyan-500/20 rounded-lg"><HeartPulse className="w-5 h-5 text-cyan-400" /></div>
            <div className="text-sm text-gray-400 uppercase tracking-widest">Health Score</div>
          </div>
          <div className="flex items-end gap-1 relative z-10">
            <div className="text-4xl font-light text-white">{data.summary.health_score}</div>
            <div className="text-xl text-gray-500 mb-1">/100</div>
          </div>
          <div className="mt-4 w-full bg-white/10 h-1.5 rounded-full overflow-hidden relative z-10">
            <div className="bg-cyan-400 h-full rounded-full shadow-[0_0_10px_rgba(34,211,238,0.8)]" style={{ width: `${data.summary.health_score}%` }}></div>
          </div>
        </div>

      </div>
    </div>
  );
}
