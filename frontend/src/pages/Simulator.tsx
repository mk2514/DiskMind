import { useEffect, useState } from 'react';
import { getRecommendations, simulate } from '../api/client';
import type { Recommendation, SimulationResult } from '../types';

export default function Simulator() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [simResult, setSimResult] = useState<SimulationResult | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);

  useEffect(() => {
    getRecommendations().then(setRecommendations).catch(console.error);
  }, []);

  const toggleSelection = (id: number) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handleSimulate = async () => {
    setIsSimulating(true);
    try {
      const result = await simulate(selectedIds);
      setSimResult(result);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-light tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400 border-b border-white/10 pb-4">What-If Simulator</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Left Col: Selections */}
        <div className="space-y-4">
          <h2 className="text-xl font-light text-white uppercase tracking-widest mb-4">Select Actions to Simulate</h2>
          {recommendations.map(rec => (
            <div 
              key={rec.id} 
              onClick={() => toggleSelection(rec.id)}
              className={`p-4 rounded-xl border cursor-pointer transition-all duration-300 ${selectedIds.includes(rec.id) ? 'bg-indigo-500/20 border-indigo-500/50 shadow-[0_0_15px_rgba(99,102,241,0.2)]' : 'bg-black/40 border-white/10 hover:bg-white/5'}`}
            >
              <div className="flex items-center gap-3">
                <input type="checkbox" checked={selectedIds.includes(rec.id)} readOnly className="w-5 h-5 accent-indigo-500" />
                <div className="flex-1">
                  <h3 className="font-medium text-white">{rec.reason}</h3>
                  <div className="text-sm text-gray-400 mt-1">Recovers {(rec.size_bytes / 1e9).toFixed(2)} GB</div>
                </div>
              </div>
            </div>
          ))}

          <button 
            onClick={handleSimulate}
            disabled={selectedIds.length === 0 || isSimulating}
            className="w-full py-4 mt-6 rounded-xl bg-indigo-500 text-white font-bold tracking-widest uppercase hover:bg-indigo-600 hover:shadow-[0_0_20px_rgba(99,102,241,0.6)] disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300"
          >
            {isSimulating ? 'Simulating...' : 'Run Simulation'}
          </button>
        </div>

        {/* Right Col: Results */}
        <div className="space-y-4">
          <h2 className="text-xl font-light text-white uppercase tracking-widest mb-4">Simulation Results</h2>
          
          {simResult ? (
            <div className="space-y-6">
              <div className="p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-lg">
                <div className="text-sm text-gray-400 uppercase tracking-widest mb-2">Projected Impact</div>
                <div className="text-4xl font-light text-emerald-300 drop-shadow-[0_0_10px_rgba(52,211,153,0.5)]">
                  +{simResult.impact.days_gained_until_90pct} days gained
                </div>
                <p className="text-gray-400 mt-2">Delays 90% capacity from Day {simResult.before.days_until_90pct} to Day {simResult.after.days_until_90pct}.</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-lg">
                  <div className="text-sm text-gray-400 uppercase tracking-widest mb-2">Before</div>
                  <div className="text-2xl font-light text-rose-300">{simResult.before.utilization_pct}% Full</div>
                </div>
                <div className="p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-lg">
                  <div className="text-sm text-gray-400 uppercase tracking-widest mb-2">After</div>
                  <div className="text-2xl font-light text-emerald-300">{simResult.after.utilization_pct}% Full</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center p-8 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-lg min-h-[300px]">
              <div className="text-6xl mb-4 opacity-50">🔬</div>
              <p className="text-gray-500 font-light text-center">Select actions on the left and run the simulator to predict how they will impact your storage timeline.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
