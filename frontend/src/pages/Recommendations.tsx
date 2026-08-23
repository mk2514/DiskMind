import { useEffect, useState } from 'react';
import { getRecommendations } from '../api/client';
import type { Recommendation } from '../types';

export default function Recommendations() {
  const [data, setData] = useState<Recommendation[]>([]);

  useEffect(() => {
    getRecommendations().then(setData).catch(console.error);
  }, []);

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-light tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400 border-b border-white/10 pb-4">AI Recommendations</h1>
      <div className="space-y-4">
        {data.map((rec) => (
          <div key={rec.id} className="p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl flex justify-between items-center hover:bg-white/5 hover:border-indigo-500/30 transition-all duration-300 group shadow-lg">
            <div>
              <h3 className="font-light text-xl text-white group-hover:text-indigo-300 transition-colors">{rec.reason}</h3>
              <p className="text-gray-400 mt-2 text-sm leading-relaxed">{rec.explanation}</p>
            </div>
            <button className="px-6 py-2.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/50 hover:bg-indigo-500 hover:text-white hover:shadow-[0_0_15px_rgba(99,102,241,0.6)] transition-all duration-300 whitespace-nowrap ml-6">
              Execute
            </button>
          </div>
        ))}
        {data.length === 0 && (
          <div className="p-12 text-center text-gray-500 font-light border border-dashed border-white/10 rounded-2xl">
            No pending recommendations. Your disk is fully optimized.
          </div>
        )}
      </div>
    </div>
  );
}
