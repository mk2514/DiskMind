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
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-black border-b border-surface-600 pb-2">Storage Overview</h1>
      <div className="grid grid-cols-3 gap-6">
        <div className="p-6 bg-surface-800 border border-surface-600">
          <div className="text-sm text-text-muted">Total Space</div>
          <div className="text-2xl font-bold text-black">{formatBytes(data.summary.total_bytes)}</div>
        </div>
        <div className="p-6 bg-surface-800 border border-surface-600">
          <div className="text-sm text-text-muted">Used Space</div>
          <div className="text-2xl font-bold text-black">{formatBytes(data.summary.used_bytes)}</div>
        </div>
        <div className="p-6 bg-surface-800 border border-surface-600">
          <div className="text-sm text-text-muted">Free Space</div>
          <div className="text-2xl font-bold text-black">{formatBytes(data.summary.free_bytes)}</div>
        </div>
        <div className="p-6 bg-surface-800 border border-surface-600">
          <div className="text-sm text-text-muted">Utilization</div>
          <div className="text-2xl font-bold text-black">{data.summary.utilization_pct}%</div>
        </div>
        <div className="p-6 bg-surface-800 border border-surface-600">
          <div className="text-sm text-text-muted">Pending AI Recommendations</div>
          <div className="text-2xl font-bold text-black">{data.summary.pending_recommendations}</div>
        </div>
        <div className="p-6 bg-surface-800 border border-surface-600">
          <div className="text-sm text-text-muted">Health Score</div>
          <div className="text-2xl font-bold text-black">{data.summary.health_score}/100</div>
        </div>
      </div>
    </div>
  );
}
