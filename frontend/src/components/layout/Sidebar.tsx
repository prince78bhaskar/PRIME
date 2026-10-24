import React from 'react';
import { Terminal, Users, CheckSquare, Sliders, Activity } from 'lucide-react';
import { ActiveTab } from '../../types';

interface SidebarProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
  const navItems: { id: ActiveTab; label: string; icon: React.ReactNode; badge?: string }[] = [
    {
      id: 'command',
      label: 'Command Center',
      icon: <Terminal className="w-5 h-5" />,
    },
    {
      id: 'agents',
      label: 'Specialist Agents',
      icon: <Users className="w-5 h-5" />,
      badge: 'PHASE 04',
    },
    {
      id: 'tasks',
      label: 'Tasks & Memory',
      icon: <CheckSquare className="w-5 h-5" />,
      badge: 'PHASE 04',
    },
    {
      id: 'settings',
      label: 'System Config',
      icon: <Sliders className="w-5 h-5" />,
    },
  ];

  return (
    <aside className="w-16 lg:w-60 border-r border-cyan-500/20 bg-hud-panel/80 backdrop-blur-md flex flex-col justify-between select-none z-10 transition-all duration-300">
      <div className="py-4 space-y-1">
        <div className="px-4 pb-3 hidden lg:block">
          <p className="text-[10px] font-mono tracking-widest text-slate-500 uppercase">
            PRIMARY MODULES
          </p>
        </div>

        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`w-full flex items-center px-4 py-3 text-sm font-medium transition-all relative group ${
                isActive
                  ? 'text-cyan-300 bg-cyan-950/40 border-r-2 border-cyan-400 shadow-inner-glow'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
              }`}
            >
              <div className={`${isActive ? 'text-cyan-400' : 'text-slate-400 group-hover:text-cyan-400'}`}>
                {item.icon}
              </div>
              <span className="ml-3 hidden lg:block tracking-wide font-display text-xs">
                {item.label}
              </span>

              {item.badge && (
                <span className="hidden lg:inline-block ml-auto text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-amber-400 border border-amber-500/30">
                  {item.badge}
                </span>
              )}

              {/* Mobile Tooltip */}
              <div className="lg:hidden absolute left-full ml-2 px-2 py-1 rounded bg-slate-900 border border-cyan-500/30 text-cyan-300 text-xs font-mono whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50">
                {item.label} {item.badge ? `(${item.badge})` : ''}
              </div>
            </button>
          );
        })}
      </div>

      {/* Bottom Telemetry & Status */}
      <div className="p-3 border-t border-cyan-500/20 hidden lg:block">
        <div className="p-3 rounded-lg bg-slate-900/60 border border-cyan-500/10 space-y-2">
          <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
            <span className="flex items-center space-x-1">
              <Activity className="w-3 h-3 text-cyan-400 animate-pulse" />
              <span>ARC PROTOCOL</span>
            </span>
            <span className="text-cyan-400">ACTIVE</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1 overflow-hidden">
            <div className="bg-gradient-to-r from-cyan-500 to-amber-400 h-1 w-3/4 animate-pulse" />
          </div>
          <div className="flex justify-between items-center text-[10px] font-mono text-slate-500">
            <span>SYS_CORE</span>
            <span>VER 0.3.0</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
