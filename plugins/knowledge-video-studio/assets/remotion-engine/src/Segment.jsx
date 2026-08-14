import React from 'react';
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'};

const baseFont = {
  fontFamily: 'Inter, "Noto Sans SC", system-ui, sans-serif',
  textRendering: 'geometricPrecision',
};

const enter = (frame, fps, delay = 0) =>
  spring({frame: Math.max(0, frame - delay), fps, config: {damping: 18, stiffness: 140, mass: 0.8}});

const KineticTitle = ({title, subtitle, foreground, accent}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const words = String(title || '').split(/\s+/).filter(Boolean);
  return (
    <div style={{padding: '0 9%', width: '100%', boxSizing: 'border-box'}}>
      <div style={{display: 'flex', flexWrap: 'wrap', gap: '0.1em 0.28em', maxWidth: 1500}}>
        {words.map((word, index) => {
          const progress = enter(frame, fps, index * 3);
          return (
            <span
              key={`${word}-${index}`}
              style={{
                ...baseFont,
                color: index === words.length - 1 ? accent : foreground,
                fontSize: 112,
                fontWeight: 800,
                lineHeight: 1.04,
                opacity: progress,
                transform: `translateY(${(1 - progress) * 58}px)`,
              }}
            >
              {word}
            </span>
          );
        })}
      </div>
      {subtitle ? (
        <div
          style={{
            ...baseFont,
            color: foreground,
            fontSize: 38,
            lineHeight: 1.35,
            maxWidth: 1050,
            marginTop: 42,
            opacity: enter(frame, fps, words.length * 3 + 8),
          }}
        >
          {subtitle}
        </div>
      ) : null}
    </div>
  );
};

const normalizeBars = (data) => {
  if (Array.isArray(data?.items)) return data.items;
  const labels = Array.isArray(data?.labels) ? data.labels : [];
  const values = Array.isArray(data?.values) ? data.values : [];
  return labels.map((label, index) => ({label, value: Number(values[index] || 0)}));
};

const BarChart = ({title, data, foreground, accent}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const items = normalizeBars(data);
  const max = Math.max(1, ...items.map((item) => Number(item.value || 0)));
  const scale = Math.min(width / 1920, height / 1080);
  const chartHeight = height * 0.44;
  const gap = Math.max(10, 34 * scale);
  return (
    <div style={{width: '82%', display: 'flex', flexDirection: 'column'}}>
      <div style={{...baseFont, color: foreground, fontSize: Math.max(22, 62 * scale), lineHeight: 1.12, fontWeight: 760, marginBottom: Math.max(18, 48 * scale)}}>{title}</div>
      <div style={{display: 'flex', alignItems: 'flex-end', gap, height: chartHeight, borderBottom: `2px solid ${foreground}33`}}>
        {items.map((item, index) => {
          const progress = enter(frame, fps, 10 + index * 5);
          const barHeight = Math.max(2, (Number(item.value || 0) / max) * chartHeight * 0.74 * progress);
          return (
            <div key={`${item.label}-${index}`} style={{flex: 1, height: chartHeight, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', alignItems: 'center'}}>
              <div style={{...baseFont, color: foreground, fontSize: Math.max(15, 34 * scale), fontWeight: 700, opacity: progress, marginBottom: Math.max(5, 12 * scale)}}>{item.value}</div>
              <div style={{width: '100%', maxWidth: 210 * Math.max(scale, 0.55), height: barHeight, background: index === items.length - 1 ? accent : `${foreground}BB`, borderRadius: `${Math.max(5, 18 * scale)}px ${Math.max(5, 18 * scale)}px 0 0`}} />
              <div style={{...baseFont, color: foreground, fontSize: Math.max(13, 27 * scale), opacity: 0.82, marginTop: Math.max(7, 18 * scale), minHeight: Math.max(20, 42 * scale), textAlign: 'center'}}>{item.label}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const Timeline = ({title, data, foreground, accent}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const items = Array.isArray(data?.items) ? data.items : [];
  const progress = interpolate(frame, [5, durationInFrames - 12], [0, 1], clamp);
  return (
    <div style={{width: '84%', height: '68%', display: 'flex', flexDirection: 'column'}}>
      <div style={{...baseFont, color: foreground, fontSize: 62, fontWeight: 760}}>{title}</div>
      <div style={{position: 'relative', flex: 1, display: 'flex', alignItems: 'center', marginTop: 40}}>
        <div style={{position: 'absolute', left: 0, right: 0, top: '50%', height: 5, background: `${foreground}28`}} />
        <div style={{position: 'absolute', left: 0, top: '50%', height: 5, width: `${progress * 100}%`, background: accent}} />
        <div style={{display: 'flex', width: '100%', justifyContent: 'space-between', position: 'relative'}}>
          {items.map((item, index) => {
            const p = enter(frame, fps, 10 + index * 8);
            const above = index % 2 === 0;
            return (
              <div key={`${item.label || item.title}-${index}`} style={{width: `${90 / Math.max(1, items.length)}%`, opacity: p, transform: `translateY(${(1 - p) * (above ? 22 : -22)}px)`}}>
                <div style={{width: 28, height: 28, borderRadius: 99, background: accent, border: `7px solid ${foreground}`, margin: '0 auto'}} />
                <div style={{...baseFont, color: foreground, textAlign: 'center', marginTop: above ? -150 : 34}}>
                  <div style={{fontSize: 26, opacity: 0.68}}>{item.label || item.time}</div>
                  <div style={{fontSize: 30, fontWeight: 720, marginTop: 8}}>{item.title || item.text}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

const Flow = ({title, data, foreground, accent}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const nodes = Array.isArray(data?.nodes) ? data.nodes : [];
  return (
    <div style={{width: '86%', display: 'flex', flexDirection: 'column', gap: 64}}>
      <div style={{...baseFont, color: foreground, fontSize: 62, fontWeight: 760}}>{title}</div>
      <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 22}}>
        {nodes.map((node, index) => {
          const label = typeof node === 'string' ? node : node.label || node.title;
          const p = enter(frame, fps, 8 + index * 8);
          return (
            <React.Fragment key={`${label}-${index}`}>
              {index ? (
                <div style={{color: accent, fontSize: 54, opacity: enter(frame, fps, 5 + index * 8), transform: 'translateY(-2px)'}}>→</div>
              ) : null}
              <div
                style={{
                  ...baseFont,
                  width: 250,
                  minHeight: 140,
                  padding: '28px 24px',
                  boxSizing: 'border-box',
                  borderRadius: 24,
                  border: `3px solid ${index === nodes.length - 1 ? accent : foreground}`,
                  color: foreground,
                  display: 'grid',
                  placeItems: 'center',
                  textAlign: 'center',
                  fontSize: 34,
                  fontWeight: 700,
                  opacity: p,
                  transform: `scale(${0.86 + p * 0.14})`,
                }}
              >
                {label}
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

const Code = ({title, data, foreground, accent}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const lines = Array.isArray(data?.lines) ? data.lines : [];
  const shown = Math.floor(interpolate(frame, [8, Math.max(9, lines.length * 8)], [0, lines.length], clamp));
  return (
    <div style={{width: '80%', display: 'flex', flexDirection: 'column', gap: 36}}>
      <div style={{...baseFont, color: foreground, fontSize: 58, fontWeight: 760}}>{title}</div>
      <div style={{background: '#080B0E', border: `2px solid ${foreground}22`, borderRadius: 26, padding: '42px 48px', boxShadow: '0 32px 90px #0008'}}>
        {lines.map((line, index) => {
          const visible = index < shown;
          return (
            <div key={`${line}-${index}`} style={{fontFamily: '"SFMono-Regular", Consolas, monospace', fontSize: 30, lineHeight: 1.62, color: index === shown - 1 ? accent : foreground, opacity: visible ? 1 : 0}}>
              <span style={{display: 'inline-block', width: 54, opacity: 0.35}}>{index + 1}</span>{line}
            </div>
          );
        })}
        <span style={{display: 'inline-block', width: 14, height: 34, background: accent, opacity: Math.floor(frame / Math.max(1, fps / 2)) % 2 ? 0.2 : 1}} />
      </div>
    </div>
  );
};

export const Segment = (props) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const fade = interpolate(frame, [0, 8, Math.max(9, durationInFrames - 8), durationInFrames - 1], [0, 1, 1, 0], clamp);
  const common = {
    title: props.title,
    subtitle: props.subtitle,
    data: props.data || {},
    foreground: props.foreground || '#F4E7C5',
    accent: props.accent || '#E6573F',
  };
  let content;
  switch (props.kind) {
    case 'bar-chart': content = <BarChart {...common} />; break;
    case 'timeline': content = <Timeline {...common} />; break;
    case 'flow': content = <Flow {...common} />; break;
    case 'code': content = <Code {...common} />; break;
    default: content = <KineticTitle {...common} />;
  }
  return (
    <AbsoluteFill style={{backgroundColor: props.background || '#101418', opacity: fade, justifyContent: 'center', alignItems: 'center', overflow: 'hidden'}}>
      <div style={{position: 'absolute', width: 620, height: 620, borderRadius: 999, background: `${common.accent}18`, filter: 'blur(90px)', right: -180, top: -180}} />
      {content}
    </AbsoluteFill>
  );
};
