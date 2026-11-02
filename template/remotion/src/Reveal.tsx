import React from 'react';
import { AbsoluteFill, Audio, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { TL } from './timeline';

const W = 1080, H = 1920, FPS = 30;
export const REVEAL_TOTAL = () => Math.round(TL.total * 30) + 18;
const FONT = '"Songti SC", "STSong", "Hiragino Sans GB", serif';
const GOLD = '#e8b45a';
const CREAM = '#f4eee2';

// 数字句：出现巨大数字，制造「仪式感数据型」的留人点
const NUM_RE = /[0-9０-９一二三四五六七八九十百千万]+/;

const Grain: React.FC = () => (
  <AbsoluteFill
    style={{
      opacity: 0.05,
      backgroundImage:
        'radial-gradient(rgba(255,255,255,.9) 0.5px, transparent 0.5px)',
      backgroundSize: '3px 3px',
      mixBlendMode: 'overlay',
    }}
  />
);

const Rings: React.FC<{ f: number }> = ({ f }) => (
  <svg width={W} height={H} style={{ position: 'absolute', opacity: 0.35 }}>
    {[0, 1, 2].map((i) => (
      <g key={i} transform={`translate(${W / 2},${H * 0.42}) rotate(${(f * (0.15 + i * 0.1)) % 360})`}>
        <circle
          r={240 + i * 78}
          fill="none"
          stroke={GOLD}
          strokeWidth={i === 0 ? 2.5 : 1.2}
          strokeDasharray={i === 1 ? '2 14' : undefined}
          opacity={0.55 - i * 0.12}
        />
      </g>
    ))}
  </svg>
);

const Line: React.FC<{ text: string; at: number; dur: number; idx: number; total: number; f: number }> = ({
  text, at, dur, idx, total, f,
}) => {
  const { fps } = useVideoConfig();
  const local = f - at;
  if (local < 0) return null;
  const enter = spring({ frame: local, fps, config: { damping: 16, mass: 0.6 } });
  const out = interpolate(local, [dur - 3, dur], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const zoom = interpolate(local, [0, dur], [1.14, 1.02]);
  const isNum = NUM_RE.test(text);
  const flash = interpolate(local, [0, 5, 12], [1, 0.45, 0], { extrapolateRight: 'clamp' });

  const mode = idx % 3; // 0 居中巨字 / 1 左侧竖线 / 2 左下大字
  const size = text.length <= 7 ? 100 : text.length <= 9 ? 88 : 78;

  return (
    <>
      <AbsoluteFill style={{ background: '#fff', opacity: flash * 0.26, mixBlendMode: 'screen' }} />
      <AbsoluteFill
        style={{
          transform: `scale(${zoom})`,
          opacity: out,
          alignItems: mode === 0 ? 'center' : 'flex-start',
          justifyContent: mode === 2 ? 'flex-end' : 'center',
          padding: mode === 0 ? '0 96px' : '0 0 0 110px',
          paddingBottom: mode === 2 ? 420 : 0,
        }}
      >
        {mode === 1 ? (
          <div style={{ position: 'absolute', left: 78, top: '22%', bottom: '22%', width: 4, background: `linear-gradient(180deg, transparent, ${GOLD}, transparent)`, opacity: 0.7 }} />
        ) : null}
        {mode === 2 ? (
          <div style={{ position: 'absolute', left: 84, top: '18%', fontFamily: FONT, fontSize: 210, color: 'rgba(232,180,90,.10)', lineHeight: 1 }}>“</div>
        ) : null}
        <div
          style={{
            fontFamily: FONT,
            fontSize: size,
            lineHeight: 1.4,
            letterSpacing: 5,
            textAlign: mode === 0 ? 'center' : 'left',
            color: isNum ? GOLD : CREAM,
            textShadow: `0 0 26px rgba(232,180,90,${isNum ? 0.55 : 0.18}), 0 4px 18px rgba(0,0,0,.8)`,
            transform: `scale(${enter})`,
            fontWeight: 500,
            maxWidth: 960,
          }}
        >
          {text}
        </div>
      </AbsoluteFill>
    </>
  );
};

export const Reveal: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const total = Math.round(TL.total * fps);

  // 背景缓慢呼吸的心跳光
  const pulse = 1 + Math.sin(f / fps * 1.6) * 0.03;

  return (
    <AbsoluteFill style={{ backgroundColor: '#0a0605' }}>
      <Audio src={staticFile('voice_v6.mp3')} />
      <Audio src={staticFile('sfx/boom.wav')} volume={0.45} />
      <AbsoluteFill
        style={{
          background: `radial-gradient(120% 90% at 50% 42%, rgba(150,60,20,.55) 0%, rgba(60,18,8,.35) 38%, rgba(10,6,5,1) 72%)`,
          transform: `scale(${pulse})`,
        }}
      />
      <Rings f={f} />
      <Grain />
      {/* 印章 */}
      <div
        style={{
          position: 'absolute', right: 76, top: 168, width: 92, height: 92,
          border: `3px solid rgba(200,60,40,.75)`, borderRadius: 10,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          transform: 'rotate(-6deg)', opacity: 0.85,
        }}
      >
        <span style={{ fontFamily: FONT, color: 'rgba(210,70,45,.9)', fontSize: 40, letterSpacing: 2 }}>肥</span>
      </div>

      {/* 顶部章节标 */}
      <div style={{ position: 'absolute', top: 150, width: '100%', textAlign: 'center', fontFamily: FONT, color: GOLD, fontSize: 30, letterSpacing: 12, opacity: 0.75 }}>
        — 大 肥 鱼 · 讲 给 你 听 —
      </div>

      {(() => {
        const t = f / fps;
        let idx = 0;
        for (let i = 0; i < TL.lines.length; i++) if (t >= TL.lines[i].s) idx = i;
        const cur = TL.lines[idx];
        const next = TL.lines[idx + 1];
        const end = next ? next.s : TL.total + 0.6;
        return (
          <Line
            key={idx}
            text={cur.text}
            at={Math.round(cur.s * fps)}
            dur={Math.round((end - cur.s) * fps)}
            idx={idx}
            total={TL.lines.length}
            f={f}
          />
        );
      })()}

      {/* 底部落款与进度 */}
      <div style={{ position: 'absolute', bottom: 110, width: '100%', display: 'flex', justifyContent: 'center', gap: 14 }}>
        {TL.lines.map((_, i) => {
          const p = f / total;
          const on = p > i / TL.lines.length;
          return <div key={i} style={{ width: 12, height: 12, borderRadius: 6, background: on ? GOLD : 'rgba(255,255,255,.18)' }} />;
        })}
      </div>
      <div style={{ position: 'absolute', bottom: 50, width: '100%', textAlign: 'center', fontFamily: FONT, color: 'rgba(244,238,226,.35)', fontSize: 22, letterSpacing: 6 }}>
        大肥鱼 · B 站
      </div>
    </AbsoluteFill>
  );
};
