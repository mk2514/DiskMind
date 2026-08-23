import { Terminal, Copy, CheckCircle, AlertCircle } from 'lucide-react';
import { useState } from 'react';

export default function SetupGuide({ error }: { error?: string }) {
  const [copied, setCopied] = useState(false);

  const command = `git clone https://github.com/mk2514/DiskMind.git
cd DiskMind
pip install -r agent/requirements.txt
export API_URL="${import.meta.env.VITE_API_URL || 'https://your-backend.onrender.com'}"
python agent/agent.py`;

  const handleCopy = () => {
    navigator.clipboard.writeText(command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] p-8">
      <div className="w-full max-w-3xl bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl overflow-hidden relative">
        <div className="absolute top-0 right-0 p-8 opacity-5">
          <Terminal size={120} />
        </div>
        
        <div className="p-8 relative z-10">
          <div className="flex items-center gap-4 mb-6">
            <div className="p-3 bg-indigo-500/20 rounded-xl">
              <Terminal className="w-8 h-8 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-2xl font-light text-white tracking-wide">Waiting for Live Data...</h2>
              <p className="text-gray-400 mt-1">Connect your Linux PC to start streaming telemetry.</p>
            </div>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-rose-300 font-medium">Connection Error</h4>
                <p className="text-rose-400/80 text-sm mt-1">{error}</p>
              </div>
            </div>
          )}

          <div className="space-y-6">
            <div className="bg-black/60 rounded-xl border border-white/5 overflow-hidden">
              <div className="flex items-center justify-between px-4 py-2 bg-white/5 border-b border-white/5">
                <div className="flex gap-2">
                  <div className="w-3 h-3 rounded-full bg-rose-500"></div>
                  <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                  <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
                </div>
                <button 
                  onClick={handleCopy}
                  className="flex items-center gap-2 text-xs text-gray-400 hover:text-white transition-colors"
                >
                  {copied ? <CheckCircle className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                  {copied ? 'Copied!' : 'Copy Commands'}
                </button>
              </div>
              <div className="p-6">
                <pre className="font-mono text-sm text-gray-300 leading-relaxed overflow-x-auto">
                  <code>{command}</code>
                </pre>
              </div>
            </div>

            <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
              <div className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></div>
              Actively polling for new connections...
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
