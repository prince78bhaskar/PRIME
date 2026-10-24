import React from 'react';
import { Mic, Volume2 } from 'lucide-react';

interface AudioWaveformProps {
  isActive?: boolean;
}

export const AudioWaveform: React.FC<AudioWaveformProps> = ({ isActive = false }) => {
  // Generate 28 audio frequency visualizer bars
  const bars = Array.from({ length: 28 }, (_, i) => {
    // Determine height pattern
    const baseHeight = Math.sin((i / 28) * Math.PI) * 75 + 15;
    const animDelay = (i * 0.05).toFixed(2);
    return { id: i, baseHeight, animDelay };
  });

  return (
    <div className="hud-panel hud-corner-brackets p-4 rounded-xl space-y-3">
      {/* Header telemetry */}
      <div className="flex items-center justify-between text-xs font-mono">
        <div className="flex items-center space-x-2 text-cyan-400">
          <Mic className="w-3.5 h-3.5" />
          <span className="font-semibold tracking-wider">SENSORY AUDIO FREQUENCY BUS</span>
        </div>
        <div className="flex items-center space-x-2 text-slate-500 text-[10px]">
          <Volume2 className="w-3 h-3 text-amber-400" />
          <span>LOCAL PUSH-TO-TALK • EN / HI</span>
        </div>
      </div>

      {/* Waveform Graphic */}
      <div className="h-14 bg-slate-950/60 rounded-lg border border-cyan-500/15 p-2 flex items-center justify-between px-3 overflow-hidden">
        {bars.map((bar) => (
          <div
            key={bar.id}
            className="w-1.5 rounded-full bg-gradient-to-t from-cyan-600 via-cyan-400 to-amber-300 transition-all duration-300"
            style={{
              height: isActive ? `${Math.max(10, Math.min(100, bar.baseHeight))}%` : '20%',
              animation: isActive ? `wave-bar 1s ease-in-out infinite` : 'none',
              animationDelay: `${bar.animDelay}s`,
            }}
          />
        ))}
      </div>

      {/* Footer info */}
      <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
        <span>MICROPHONE ACTIVE ONLY WHILE PRESSED</span>
        <span className="text-cyan-400/70">NO WAKE WORD / NO CLOUD AUDIO</span>
      </div>
    </div>
  );
};
