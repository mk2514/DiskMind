import { useEffect, useState } from 'react';
import { getForecast } from '../api/client';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import type { Forecast as ForecastType } from '../types';

function formatBytes(bytes: number) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export default function Forecast() {
  const [data, setData] = useState<ForecastType | null>(null);

  useEffect(() => {
    getForecast().then(setData).catch(console.error);
  }, []);

  if (!data) return <div className="p-8 text-gray-500">Loading forecast data...</div>;

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-light tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400 border-b border-white/10 pb-4">Storage Forecast</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-lg">
          <div className="text-sm text-gray-400 uppercase tracking-widest mb-2">Daily Growth Rate</div>
          <div className="text-3xl font-light text-rose-300 drop-shadow-[0_0_10px_rgba(244,63,94,0.5)]">
            +{formatBytes(data.avg_daily_growth_bytes)}/day
          </div>
        </div>
        <div className="p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-lg">
          <div className="text-sm text-gray-400 uppercase tracking-widest mb-2">Days to 90% Capacity</div>
          <div className="text-3xl font-light text-amber-300 drop-shadow-[0_0_10px_rgba(251,191,36,0.5)]">
            {data.thresholds.days_until_90pct} days
          </div>
        </div>
        <div className="p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-lg">
          <div className="text-sm text-gray-400 uppercase tracking-widest mb-2">Days to 100% Capacity</div>
          <div className="text-3xl font-light text-rose-500 drop-shadow-[0_0_10px_rgba(244,63,94,0.8)] font-bold">
            {data.thresholds.days_until_100pct} days
          </div>
        </div>
      </div>

      <div className="p-8 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl">
        <h2 className="text-xl font-light text-white mb-6 uppercase tracking-widest">30-Day Predictive Model ({data.model_type.replace('_', ' ')})</h2>
        <div className="h-[400px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.daily_series} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="day" stroke="#9ca3af" tickFormatter={(val) => `Day ${val}`} />
              <YAxis stroke="#9ca3af" domain={['auto', 100]} tickFormatter={(val) => `${val}%`} />
              <Tooltip 
                contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '12px' }}
                formatter={(value: any) => [`${Number(value).toFixed(2)}%`, 'Utilization']}
                labelFormatter={(label) => `Day ${label}`}
              />
              <ReferenceLine y={90} stroke="#f59e0b" strokeDasharray="3 3" label={{ position: 'insideTopLeft', value: '90% Warning', fill: '#f59e0b' }} />
              <ReferenceLine y={100} stroke="#ef4444" strokeDasharray="3 3" label={{ position: 'insideTopLeft', value: '100% Critical', fill: '#ef4444' }} />
              <Line type="monotone" dataKey="utilization_pct" stroke="#6366f1" strokeWidth={3} dot={false} activeDot={{ r: 8, fill: '#6366f1', stroke: '#fff' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
