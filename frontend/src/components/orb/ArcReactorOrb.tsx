import React from 'react';

interface ArcReactorOrbProps {
  isStreaming: boolean;
  isConnected: boolean;
  hasError?: boolean;
}

export const ArcReactorOrb: React.FC<ArcReactorOrbProps> = ({
  isStreaming,
  isConnected,
  hasError,
}) => {
  // Determine primary color theme based on state
  const colorTheme = hasError
    ? {
        glow: 'shadow-glow-crimson',
        border: 'border-rose-500/50',
        text: 'text-rose-400',
        stroke: '#ef4444',
        coreBg: 'from-rose-500 via-rose-900 to-black',
        statusText: 'TELEMETRY WARNING',
      }
    : !isConnected
    ? {
        glow: 'shadow-glow-amber',
        border: 'border-amber-500/50',
        text: 'text-amber-400',
        stroke: '#f59e0b',
        coreBg: 'from-amber-500 via-amber-950 to-black',
        statusText: 'STANDBY • DAEMON OFFLINE',
      }
    : isStreaming
    ? {
        glow: 'shadow-glow-cyan-lg',
        border: 'border-cyan-400',
        text: 'text-cyan-300',
        stroke: '#00f0ff',
        coreBg: 'from-cyan-300 via-cyan-700 to-black',
        statusText: 'PROCESSING TOKEN STREAM',
      }
    : {
        glow: 'shadow-glow-cyan',
        border: 'border-cyan-500/40',
        text: 'text-cyan-400',
        stroke: '#00f0ff',
        coreBg: 'from-cyan-400 via-cyan-900 to-black',
        statusText: 'P.R.I.M.E. CORE • READY',
      };

  return (
    <div className="relative flex flex-col items-center justify-center p-6 select-none">
      {/* Outer Ambient Glow Effect */}
      <div
        className={`absolute w-72 h-72 sm:w-80 sm:h-80 rounded-full blur-3xl opacity-20 pointer-events-none transition-all duration-700 ${
          isStreaming ? 'scale-110 opacity-35 bg-cyan-400' : 'bg-cyan-500'
        }`}
      />

      {/* Main Reactor Assembly */}
      <div className="relative w-64 h-64 sm:w-72 sm:h-72 flex items-center justify-center">
        {/* Layer 1: Outer Tachometer / Telemetry Ring (Static) */}
        <div className="absolute inset-0 rounded-full border border-cyan-500/15" />

        {/* Layer 2: Segmented Outer Rotating Ring */}
        <svg
          className={`absolute inset-0 w-full h-full ${
            isStreaming ? 'animate-spin-medium' : 'animate-spin-slow'
          } transition-all duration-500`}
          viewBox="0 0 200 200"
        >
          {/* Segmented Outer Arcs */}
          <circle
            cx="100"
            cy="100"
            r="92"
            fill="none"
            stroke={colorTheme.stroke}
            strokeWidth="1.5"
            strokeDasharray="4 8"
            opacity="0.4"
          />
          <circle
            cx="100"
            cy="100"
            r="86"
            fill="none"
            stroke={colorTheme.stroke}
            strokeWidth="2.5"
            strokeDasharray="25 15 5 15 40 20"
            opacity="0.75"
          />
        </svg>

        {/* Layer 3: Counter-Rotating Ring with Cardinal Brackets */}
        <svg
          className={`absolute inset-4 w-[calc(100%-2rem)] h-[calc(100%-2rem)] ${
            isStreaming ? 'animate-spin-reverse-slow' : 'animate-spin-reverse-slow'
          }`}
          viewBox="0 0 160 160"
        >
          <circle
            cx="80"
            cy="80"
            r="72"
            fill="none"
            stroke={colorTheme.stroke}
            strokeWidth="1"
            strokeDasharray="2 6"
            opacity="0.3"
          />
          {/* 4 Cardinal Triangular Markers */}
          <polygon points="80,4 84,12 76,12" fill={colorTheme.stroke} opacity="0.8" />
          <polygon points="80,156 84,148 76,148" fill={colorTheme.stroke} opacity="0.8" />
          <polygon points="4,80 12,84 12,76" fill={colorTheme.stroke} opacity="0.8" />
          <polygon points="156,80 148,84 148,76" fill={colorTheme.stroke} opacity="0.8" />
        </svg>

        {/* Layer 4: Segmented Turbine Vanes */}
        <div className="absolute inset-8 rounded-full border border-cyan-500/20 flex items-center justify-center">
          {[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330].map((deg) => (
            <div
              key={deg}
              className="absolute w-full h-[1px] bg-gradient-to-r from-transparent via-cyan-500/20 to-transparent"
              style={{ transform: `rotate(${deg}deg)` }}
            />
          ))}
        </div>

        {/* Layer 5: Inner Core Chamber with Glowing Energy Pulse */}
        <div
          className={`relative w-28 h-28 sm:w-32 sm:h-32 rounded-full flex flex-col items-center justify-center border-2 ${
            colorTheme.border
          } bg-gradient-to-br ${colorTheme.coreBg} ${colorTheme.glow} transition-all duration-500 ${
            isStreaming ? 'animate-pulse scale-105' : 'animate-pulse-glow'
          }`}
        >
          {/* Central Holographic Glyphs */}
          <div className="relative z-10 text-center">
            <div className="text-[10px] font-mono tracking-widest text-white/80 font-bold">
              PRIME
            </div>
            <div className={`text-[13px] font-display font-black tracking-wider ${colorTheme.text}`}>
              {isStreaming ? 'ACTIVE' : isConnected ? 'ONLINE' : 'STANDBY'}
            </div>
            <div className="text-[8px] font-mono text-cyan-200/60 mt-0.5">
              4GB VRAM BUD
            </div>
          </div>

          {/* Central Core Point */}
          <div className="absolute w-3 h-3 rounded-full bg-white shadow-glow-cyan animate-ping opacity-75" />
        </div>
      </div>

      {/* Under-Orb Status Telemetry */}
      <div className="mt-4 flex flex-col items-center space-y-1">
        <div className={`text-xs font-mono font-bold tracking-widest ${colorTheme.text} flex items-center space-x-2`}>
          <span className={`w-2 h-2 rounded-full ${isStreaming ? 'bg-cyan-400 animate-ping' : isConnected ? 'bg-cyan-400' : 'bg-amber-400'}`} />
          <span>{colorTheme.statusText}</span>
        </div>
        <p className="text-[11px] font-mono text-slate-500 tracking-wider">
          SOVEREIGN LOCAL INFERENCE PROTOCOL
        </p>
      </div>
    </div>
  );
};
