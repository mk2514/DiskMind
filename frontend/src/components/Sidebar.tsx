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
    <div className="w-64 bg-surface-800 border-r border-surface-600 flex flex-col h-screen">
      <div className="p-6 flex items-center gap-3 border-b border-surface-600">
        <Sparkles className="w-6 h-6 text-black" />
        <div className="text-black font-bold text-lg leading-tight">DiskMind</div>
      </div>
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-none font-medium transition-all ${
                isActive
                  ? 'bg-black text-white'
                  : 'text-text-muted hover:bg-surface-700 hover:text-black'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            {item.name}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-surface-600 text-xs text-text-muted">
        DiskMind MVP v1.0
      </div>
    </div>
  );
}
