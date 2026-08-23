export default function Forecast() {
  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-light tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400 border-b border-white/10 pb-4">Storage Forecast</h1>
      <div className="p-8 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl flex items-center justify-center min-h-[400px]">
        <p className="text-gray-500 font-light tracking-widest uppercase">AI predictions and anomaly detection graphs will appear here.</p>
      </div>
    </div>
  );
}
