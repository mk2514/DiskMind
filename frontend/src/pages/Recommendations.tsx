import { useEffect, useState } from 'react';
import { getRecommendations } from '../api/client';
import type { Recommendation } from '../types';

export default function Recommendations() {
  const [data, setData] = useState<Recommendation[]>([]);

  useEffect(() => {
    getRecommendations().then(setData).catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-black border-b border-surface-600 pb-2">AI Recommendations</h1>
      <div className="space-y-4">
        {data.map((rec) => (
          <div key={rec.id} className="p-6 bg-surface-800 border border-surface-600 flex justify-between items-center">
            <div>
              <h3 className="font-bold text-lg">{rec.reason}</h3>
              <p className="text-text-muted mt-1">{rec.explanation}</p>
            </div>
            <button className="px-4 py-2 bg-black text-white hover:bg-gray-800 transition-colors">
              Execute
            </button>
          </div>
        ))}
        {data.length === 0 && (
          <div className="p-6 text-text-muted">No pending recommendations.</div>
        )}
      </div>
    </div>
  );
}
