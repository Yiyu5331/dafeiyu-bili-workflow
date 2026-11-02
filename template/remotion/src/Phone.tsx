import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Easing,
} from 'remotion';

import { TL } from './timeline';

const W = 1080;
const H = 1920;
export const FPS = 30;
export const TOTAL = Math.round(TL.total * FPS);

const FONT = '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif';
const BG = '#05070D';
const CYAN = '#5EE1FF';
const GOLD = '#FFC94D';
const RED = '#FF4D6D';

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
const lerp = (a: number, b: number, p: number) => a + (b - a) * p;
const easeOut = (p: number) => 1 - Math.pow(1 - p, 3);

const LINES = TL.lines;

const at = (t: number) => Math.round(t * FPS);

/* ───────── 状态栏 / 底栏 ───────── */

const StatusBar: React.FC<{clock: string}> = ({clock}) => (
  <div
    style={{
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      height: 110,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 52px',
      fontFamily: FONT,
      fontSize: 34,
      fontWeight: 700,
      color: '#fff',
      zIndex: 40,
    }}
  >
    <span>{clock}</span>
    <span style={{display: 'flex', gap: 10, alignItems: 'center', fontSize: 26}}>
      <span>5G</span>
      <span style={{width: 34, height: 18, border: '2px solid #fff', borderRadius: 4, display: 'inline-block'}}>
        <span style={{display: 'block', width: '72%', height: '100%', background: '#fff'}} />
      </span>
    </span>
  </div>
);

const TabBar: React.FC<{active?: number}> = ({active = 0}) => {
  const items = ['首页', '推荐', '关注', '我的'];
  return (
    <div
      style={{
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        height: 130,
        background: 'rgba(6,8,14,0.92)',
        borderTop: '1px solid rgba(255,255,255,0.08)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-around',
        fontFamily: FONT,
        fontSize: 30,
        color: 'rgba(255,255,255,0.45)',
        zIndex: 40,
      }}
    >
      {items.map((t, i) => (
        <span key={t} style={{color: i === active ? '#fff' : 'rgba(255,255,255,0.4)', fontWeight: i === active ? 800 : 500}}>
          {t}
        </span>
      ))}
    </div>
  );
};

/* ───────── 信息流卡片 ───────── */

const CARDS = [
  {u: '深夜食堂', t: '凌晨的便利店 关东煮冒着热气', g: ['#2B1B3D', '#7A3B2E'], likes: '12.3万'},
  {u: '通勤日记', t: '地铁上 每个人都低着头', g: ['#122B3D', '#1E5F6E'], likes: '8.9万'},
  {u: '游戏切片', t: '这波反杀 你看清了吗', g: ['#1A1030', '#4A2B7A'], likes: '21.7万'},
  {u: '猫猫日常', t: '它把爪子搭在我手机上', g: ['#2D2416', '#8A6B32'], likes: '33.1万'},
  {u: '冷知识', t: '为什么你记不住刚刷过的东西', g: ['#0E2430', '#2F6B7A'], likes: '5.6万'},
  {u: '情绪树洞', t: '今天也没人找我说话', g: ['#241019', '#6E2B3F'], likes: '9.4万'},
];

const FeedCard: React.FC<{c: (typeof CARDS)[0]; h?: number}> = ({c, h = 1080}) => (
  <div style={{height: h, position: 'relative', overflow: 'hidden', borderBottom: '1px solid rgba(255,255,255,0.06)'}}>
    <div style={{position: 'absolute', inset: 0, background: `linear-gradient(160deg, ${c.g[0]}, ${c.g[1]})`}} />
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundImage: 'radial-gradient(700px 700px at 30% 20%, rgba(255,255,255,0.14), transparent 65%)',
      }}
    />
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, padding: '40px 48px 56px', background: 'linear-gradient(180deg, transparent, rgba(0,0,0,0.75))'}}>
      <div style={{fontFamily: FONT, fontSize: 40, fontWeight: 800, color: '#fff'}}>@{c.u}</div>
      <div style={{fontFamily: FONT, fontSize: 34, color: 'rgba(255,255,255,0.82)', marginTop: 12}}>{c.t}</div>
      <div style={{fontFamily: FONT, fontSize: 28, color: 'rgba(255,255,255,0.6)', marginTop: 18}}>♥ {c.likes} · 评论 2,341 · 分享 876</div>
    </div>
  </div>
);

const Feed: React.FC<{offset: number; speedLines?: boolean}> = ({offset, speedLines}) => (
  <div style={{position: 'absolute', top: 110, left: 0, right: 0, bottom: 130, overflow: 'hidden'}}>
    <div style={{transform: `translateY(${-offset}px)`}}>
      {[...CARDS, ...CARDS].map((c, i) => (
        <FeedCard key={i} c={c} />
      ))}
    </div>
    {speedLines && (
      <div style={{position: 'absolute', inset: 0, backgroundImage: 'repeating-linear-gradient(0deg, rgba(255,255,255,0.05) 0 2px, transparent 2px 26px)', opacity: 0.5}} />
    )}
    <div style={{position: 'absolute', right: 34, bottom: 220, display: 'flex', flexDirection: 'column', gap: 34, alignItems: 'center', zIndex: 20}}>
      {['♥ 12.3万', '💬 2341', '↗ 876'].map((s) => (
        <div key={s} style={{fontFamily: FONT, fontSize: 26, color: '#fff', textShadow: '0 2px 10px rgba(0,0,0,0.6)'}}>{s}</div>
      ))}
    </div>
  </div>
);

/* ───────── 手势 / 双击爱心 ───────── */

const DoubleTap: React.FC<{delay: number}> = ({delay}) => {
  const f = useCurrentFrame();
  const p = clamp01((f - delay) / 26);
  if (p <= 0) return null;
  const hearts = [0, 1, 2, 3, 4, 5, 6];
  return (
    <>
      {hearts.map((i) => {
        const ang = (i / hearts.length) * Math.PI * 2;
        const r = 30 + p * 260;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: W / 2 + Math.cos(ang) * r,
              top: 960 + Math.sin(ang) * r,
              fontSize: 54 + (i % 3) * 12,
              opacity: (1 - p) * 0.95,
              transform: `scale(${1 + p * 0.5})`,
              zIndex: 30,
            }}
          >
            {i % 2 ? '💙' : '❤️'}
          </div>
        );
      })}
      <div
        style={{
          position: 'absolute',
          left: W / 2 - 90,
          top: 960 - 80,
          width: 180,
          height: 180,
          borderRadius: 90,
          border: `4px solid rgba(255,255,255,${(1 - p) * 0.8})`,
          transform: `scale(${1 + p * 2})`,
          zIndex: 29,
        }}
      />
    </>
  );
};

/* ───────── 算法节点图 ───────── */

const Algo: React.FC = () => {
  const f = useCurrentFrame();
  const nodes = [
    {x: 180, y: 780, label: '你停在哪'},
    {x: 540, y: 640, label: '兴趣画像'},
    {x: 880, y: 780, label: '下一条'},
    {x: 540, y: 1150, label: '再推一次'},
  ];
  return (
    <AbsoluteFill style={{background: BG}}>
      <svg width={W} height={H} style={{position: 'absolute', inset: 0}}>
        {nodes.map((n, i) => {
          const n2 = nodes[(i + 1) % nodes.length];
          const p = clamp01((f - 10 - i * 10) / 22);
          return (
            <line
              key={i}
              x1={n.x}
              y1={n.y}
              x2={lerp(n.x, n2.x, p)}
              y2={lerp(n.y, n2.y, p)}
              stroke={i % 2 ? GOLD : CYAN}
              strokeWidth={3}
              strokeDasharray="12 10"
              opacity={0.85}
            />
          );
        })}
      </svg>
      {nodes.map((n, i) => {
        const s = spring({frame: f - 6 - i * 8, fps: FPS, config: {damping: 12}});
        return (
          <div
            key={n.label}
            style={{
              position: 'absolute',
              left: n.x - 120,
              top: n.y - 56,
              width: 240,
              height: 112,
              borderRadius: 56,
              background: 'rgba(10,16,28,0.92)',
              border: `2px solid ${i % 2 ? GOLD : CYAN}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: FONT,
              fontSize: 34,
              fontWeight: 800,
              color: i % 2 ? GOLD : CYAN,
              transform: `scale(${s})`,
              boxShadow: `0 0 30px ${i % 2 ? GOLD : CYAN}44`,
            }}
          >
            {n.label}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

/* ───────── 时钟 ───────── */

const BigClock: React.FC<{from: string; to?: string; span?: number}> = ({from, to, span = 90}) => {
  const f = useCurrentFrame();
  const [fh, fm] = from.split(':').map(Number);
  let label = from;
  if (to) {
    const [th, tm] = to.split(':').map(Number);
    const a = fh * 60 + fm;
    const b = th * 60 + tm;
    const v = Math.round(lerp(a, b, clamp01(f / span)));
    label = `${String(Math.floor(v / 60) % 24).padStart(2, '0')}:${String(v % 60).padStart(2, '0')}`;
  }
  return (
    <div
      style={{
        fontFamily: FONT,
        fontSize: 190,
        fontWeight: 900,
        color: '#fff',
        letterSpacing: 6,
        textShadow: '0 0 60px rgba(94,225,255,0.45)',
      }}
    >
      {label}
    </div>
  );
};

/* ───────── 大字幕 ───────── */

const Caption: React.FC<{text: string; delay: number}> = ({text, delay}) => {
  const f = useCurrentFrame();
  const p = clamp01((f - delay) / 8);
  const s = spring({frame: f - delay, fps: FPS, config: {damping: 14, mass: 0.6}});
  return (
    <div
      style={{
        position: 'absolute',
        left: 60,
        right: 60,
        top: 1150,
        textAlign: 'center',
        fontFamily: FONT,
        fontSize: text.length > 9 ? 76 : 96,
        fontWeight: 900,
        color: '#fff',
        opacity: p,
        transform: `translateY(${(1 - s) * 40}px)`,
        textShadow: '0 6px 26px rgba(0,0,0,0.85), 0 0 40px rgba(94,225,255,0.25)',
        letterSpacing: 2,
        zIndex: 45,
      }}
    >
      {text}
    </div>
  );
};

/* ───────── 大肥鱼旁白角标 ───────── */

const Narrator: React.FC<{expr?: string; speaking?: boolean}> = ({speaking = true}) => {
  const f = useCurrentFrame();
  const bob = Math.sin(f / 12) * 6;
  const pulse = speaking ? 1 + Math.sin(f / 6) * 0.012 : 1;
  // 想换成自己的形象：把 public/narrator.png 放进去就会自动用图
  const hasImg = true;
  return (
    <div style={{position: 'absolute', left: 30, bottom: 150, zIndex: 46}}>
      {hasImg ? (
        <Img
          src={staticFile('narrator.png')}
          style={{width: 230, transform: `translateY(${bob}px) scale(${pulse})`,
                  filter: 'drop-shadow(0 12px 26px rgba(0,0,0,0.7))'}}
        />
      ) : null}
    </div>
  );
};

/* ───────── 倒扣手机 ───────── */

const FlipEnd: React.FC = () => {
  const f = useCurrentFrame();
  const p = clamp01(f / 26);
  const e = easeOut(p);
  const dark = clamp01(f / 40);
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `perspective(1400px) rotateX(${e * 168}deg) scale(${1 - e * 0.35})`,
          background: 'linear-gradient(160deg,#101728,#39405A)',
          borderRadius: 0,
        }}
      >
        <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(700px 700px at 50% 30%, rgba(94,225,255,0.18), transparent 70%)'}} />
      </div>
      <AbsoluteFill style={{background: `rgba(0,0,0,${dark * 0.75})`}} />
      <AbsoluteFill style={{display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 26}}>
        <div style={{fontFamily: FONT, fontSize: 58, color: 'rgba(255,255,255,0.55)', letterSpacing: 12, opacity: clamp01((f - 18) / 14)}}>
          屏幕朝下
        </div>
        <div style={{fontFamily: FONT, fontSize: 116, fontWeight: 900, color: '#fff', opacity: clamp01((f - 26) / 14)}}>
          明天再说
        </div>
        <div style={{fontFamily: FONT, fontSize: 34, color: 'rgba(255,255,255,0.45)', marginTop: 20, opacity: clamp01((f - 40) / 16)}}>
          大肥鱼 · 陪你早点睡
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/* ───────── 主合成 ───────── */

const Shot: React.FC<{from: number; dur: number; children: React.ReactNode}> = ({from, dur, children}) => (
  <Sequence from={from} durationInFrames={dur}>
    <AbsoluteFill>{children}</AbsoluteFill>
  </Sequence>
);

export const Main: React.FC = () => {
  const f = useCurrentFrame();
  // 滚动总量（多次上滑）
  const scroll = interpolate(f, [0, 40, 120, 200, 300, 420, 520], [0, 180, 520, 900, 1500, 2100, 2600], {
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.2, 0.8, 0.2, 1),
  });
  const flipStart = at(TL.flipStart);
  const flipping = f >= flipStart;

  return (
    <AbsoluteFill style={{background: BG, fontFamily: FONT}}>
      <Audio src={staticFile('voice_v6.mp3')} />

      {!flipping && (
        <>
          <Feed offset={scroll} speedLines={f > at(TL.swipeA) && f < at(TL.swipeB)} />
          <StatusBar clock={f > at(TL.flipStart) ? '02:47' : '01:29'} />
          <TabBar active={f > at(TL.lines[1].s) ? 1 : 0} />
          <DoubleTap delay={at(TL.lines[2].s)} />
        </>
      )}

      {/* 算法图：8.45-10.5 */}
      <Shot from={at(TL.algoStart)} dur={at(TL.algoDur)}>
        <Algo />
      </Shot>

      {/* 时钟：开头与结尾 */}
      <Shot from={at(0)} dur={at(TL.hookEnd)}>
        <AbsoluteFill style={{background: '#05070D', alignItems: 'center', justifyContent: 'center'}}>
          <BigClock from="01:29" />
          <div style={{fontFamily: FONT, fontSize: 40, color: 'rgba(255,255,255,0.5)', marginTop: 30}}>电量 12%</div>
        </AbsoluteFill>
      </Shot>

      <Shot from={at(TL.clockStart)} dur={at(TL.clockDur)}>
        <AbsoluteFill style={{background: '#05070D', alignItems: 'center', justifyContent: 'center'}}>
          <BigClock from="01:29" to="02:47" span={20} />
        </AbsoluteFill>
      </Shot>

      {/* 结尾倒扣 */}
      <Shot from={flipStart} dur={TOTAL - flipStart}>
        <FlipEnd />
      </Shot>

      {/* 台词字幕 */}
      {LINES.map((ln, i) => {
        const s = ln.s, e = ln.e, text = ln.text;
        const hit = i === 11;
        if (hit) return null;
        return (
          <Sequence key={i} from={at(s)} durationInFrames={at(e) - at(s) + 6}>
            <Caption text={text} delay={0} />
          </Sequence>
        );
      })}

      {(f > at(TL.algoStart) && f < at(TL.swipeA + 0.4)) || f > at(TL.flipStart) ? (
        <Narrator expr={f > at(TL.flipStart) ? 'sleepy' : 'think'} speaking />
      ) : null}
    </AbsoluteFill>
  );
};
