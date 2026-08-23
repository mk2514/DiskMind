import { NavLink } from 'react-router-dom';
import { Home, Folder, LineChart, ShieldAlert, Sparkles, MessageSquare } from 'lucide-react';

const NAV_ITEMS = [
  { name: 'Overview', path: '/overview', icon: Home },
  { name: 'Explorer', path: '/explorer', icon: Folder },
  { name: 'Forecast', path: '/forecast', icon: LineChart },
  { name: 'Recommendations', path: '/recommendations', icon: ShieldAlert },
  { name: 'Simulator', path: '/simulator', icon: Sparkles },
  { name: 'AI Copilot', path: '/chat', icon: MessageSquare },
];

export default function Sidebar() {
  return (
    <div className="w-64 bg-black/40 backdrop-blur-md border-r border-white/10 flex flex-col h-screen">
      <div className="p-6 flex items-center gap-3 border-b border-white/10">
        <Sparkles className="w-6 h-6 text-indigo-400 drop-shadow-[0_0_10px_rgba(99,102,241,0.8)]" />
        <div className="text-white font-bold text-xl tracking-wider uppercase drop-shadow-md">DiskMind</div>
      </div>
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-all duration-300 ${
                isActive
                  ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 shadow-[0_0_15px_rgba(99,102,241,0.15)]'
                  : 'text-gray-400 hover:bg-white/5 hover:text-white border border-transparent'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            {item.name}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-white/10 text-xs text-gray-500 text-center tracking-widest uppercase">
        DiskMind MVP v1.0
      </div>
    </div>
  );
}
