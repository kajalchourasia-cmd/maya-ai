"use client";

import { useId, useRef, useState, type PointerEvent } from "react";
import styles from "./weekly-guidance.module.css";

// Adapted from the existing maya-maternal-companion hormone-data.ts design.
// These hand-drawn, normalised anchors describe broad patterns only. They are
// not lab data, comparable concentrations, predictions or input to guidance.
const curves = [
  { name: "hCG", color: "#b75a7d", description: "Rises early, peaks around the end of the first trimester, then falls to a lower level.", anchors: [[1,0],[3,0],[4,10],[6,44],[8,83],[10,100],[12,72],[16,28],[22,13],[30,15],[40,22]] },
  { name: "Progesterone", color: "#7770ad", description: "Generally increases as pregnancy progresses.", anchors: [[1,9],[4,16],[8,21],[12,26],[20,43],[28,65],[34,82],[40,98]] },
  { name: "Estrogen", color: "#b68b40", description: "The broad estradiol pattern rises as pregnancy progresses.", anchors: [[1,5],[5,8],[10,13],[14,24],[20,40],[28,65],[34,83],[40,100]] },
];
const phases = [{label:"First trimester",start:1,end:13},{label:"Second trimester",start:14,end:27},{label:"Third trimester",start:28,end:42}];
const hormoneRoles = ['supports early pregnancy', 'helps maintain pregnancy', 'supports pregnancy-related growth'];
const x = (week: number) => 18 + (Math.max(1, Math.min(40, week)) - 1) / 39 * 524;
function curveY(anchors: number[][], week: number) {
  const next = anchors.findIndex(a => a[0] >= week);
  const b = anchors[next < 0 ? anchors.length - 1 : next];
  const a = anchors[Math.max(0, next - 1)];
  const t = b[0] === a[0] ? 0 : (week-a[0])/(b[0]-a[0]);
  return 132-(a[1]+(b[1]-a[1])*t*t*(3-2*t))*.98;
}
// Hit-testing uses the same curve interpolation as rendering, including grey
// segments. This is a visual explanation, not a hormone measurement.
export function hormoneAtPoint(week: number, y: number) {
  if (week < 1 || week > 40) return null;
  const distances = curves.map(c => Math.abs(curveY(c.anchors, week)-y));
  const nearest = distances.indexOf(Math.min(...distances));
  return distances[nearest] <= 10 ? nearest : null;
}
export function hormoneTooltipPosition(pointerX: number, pointerY: number, chartWidth: number) {
  const width = Math.min(310, Math.max(0, chartWidth - 16));
  return { left: Math.max(8, Math.min(pointerX + 12, chartWidth - width - 8)), top: pointerY + 14, width };
}
function path(anchors: number[][]) {
  return Array.from({length:157}, (_,i) => {
    const week = 1 + i / 4;
    return `${i ? 'L' : 'M'}${x(week).toFixed(2)},${curveY(anchors,week).toFixed(2)}`;
  }).join(' ');
}

export function JourneyHormones({ start, end, approximate }: {start:number;end:number;approximate:boolean}) {
  const id = useId().replace(/:/g, '');
  const [selected, setSelected] = useState(Math.min(40,start));
  const [hover, setHover] = useState<number | null>(null);
  const [hoverHormone, setHoverHormone] = useState<number | null>(null);
  const [focusedHormone, setFocusedHormone] = useState<number | null>(null);
  const chartRef = useRef<HTMLDivElement>(null);
  const [tooltipPosition, setTooltipPosition] = useState<ReturnType<typeof hormoneTooltipPosition> | null>(null);
  function followPointer(event: PointerEvent<HTMLElement | SVGSVGElement>) {
    const box = chartRef.current?.getBoundingClientRect();
    if (box) setTooltipPosition(hormoneTooltipPosition(event.clientX-box.left,event.clientY-box.top,box.width));
  }
  const explainedHormone = hoverHormone ?? focusedHormone;
  const exploring = hover ?? selected;
  const education = [
    {name:'hCG',body:'Helps sustain progesterone production early in pregnancy. Its broad pattern rises early, then settles lower.'},
    {name:'Progesterone',body:'Supports the uterine lining and maintenance of pregnancy. It is not a measure of calmness.'},
    {name:'Estrogen',body:'Supports pregnancy-related tissue changes. A rising curve does not predict how happy or energetic you feel.'},
    {name:'Relaxin',body:'Rises in early pregnancy and declines in the second trimester. Its roles are complex; it is not an exercise-readiness score.'},
    {name:'Prolactin',body:'Participates in breast preparation for feeding. This chart does not plot prolactin or estimate your ability to breastfeed.'},
  ];
  const active = phases.filter(p => start <= p.end && end >= p.start);
  const scaleWeeks = [1,14,28,40].filter(w => approximate || Math.abs(w-Math.min(40,start)) > 1);
  return <section className={styles.hormones} aria-label="Educational hormone patterns">
    <header className={styles.journeyChartHeader}>
      <span className={styles.journeyEyebrow}>YOUR JOURNEY</span>
      <output className={styles.exploringLabel}>{approximate ? `Weeks ${start}–${end}` : `Week ${start}`}<span aria-hidden="true"> · </span>{active.map(p=>p.label).join(' / ')}</output>
      <h2>Your body’s changing rhythm</h2>
      <p className={styles.chartHint}>Explore the hormone patterns that support pregnancy, week by week.</p>
      <div className={styles.hormoneLegend}><b>Hormones</b>{curves.map((c,i) => <button type="button" key={c.name} aria-label={`${c.name} (${hormoneRoles[i]})`} aria-describedby={explainedHormone === i ? `${id}-explanation` : undefined} onFocus={()=>{setFocusedHormone(i);setTooltipPosition(null);}} onBlur={()=>setFocusedHormone(null)} onPointerEnter={event=>{setHoverHormone(i);followPointer(event);}} onPointerMove={followPointer} onPointerLeave={()=>{setHoverHormone(null);setTooltipPosition(null);}} onClick={()=>setFocusedHormone(i)}><i style={{background:c.color}} />{c.name}</button>)}</div>
    </header>
    {approximate ? <p className={styles.rangeNote}>Weeks {start}–{end} · approximate</p> : null}
    <div ref={chartRef} className={styles.hormoneChart}>
    {explainedHormone !== null ? <div id={`${id}-explanation`} role="tooltip" style={tooltipPosition ?? undefined} className={styles.hormoneTooltip}><i style={{background:curves[explainedHormone].color}} /><span><b>{curves[explainedHormone].name}</b> ({hormoneRoles[explainedHormone]})</span></div> : null}
    <svg viewBox="0 0 560 146" role="img" onPointerLeave={()=>{setHover(null);setHoverHormone(null);setTooltipPosition(null);}} onPointerMove={event=>{const box=event.currentTarget.getBoundingClientRect();const week=1+((event.clientX-box.left)/box.width*560-18)/524*39;setHover(Math.round(Math.max(1,Math.min(40,week))));setHoverHormone(hormoneAtPoint(week,(event.clientY-box.top)/box.height*146));followPointer(event);}} aria-label={`Schematic hormone patterns, not measured levels. ${active.map(p=>p.label).join(' and ')} highlighted. ${approximate ? 'Week range is approximate.' : `Current week ${start}.`}`}>
      <defs><clipPath id={id}>{active.map(p=><rect key={p.label} x={x(p.start)} y="20" width={x(p.end === 13 ? 14 : p.end === 27 ? 28 : 40)-x(p.start)} height="119" />)}</clipPath></defs>
      {active.map(p=><rect key={p.label} x={x(p.start)} y="20" width={x(p.end === 13 ? 14 : p.end === 27 ? 28 : 40)-x(p.start)} height="119" rx="5" className={styles.hormoneBand} />)}
      {[14,28].map(w=><line key={w} x1={x(w)} x2={x(w)} y1="20" y2="139" stroke="currentColor" opacity=".13" strokeDasharray="3 5" />)}
      {curves.map((c,i)=><g key={c.name}><path d={path(c.anchors)} fill="none" stroke="currentColor" opacity=".17" strokeWidth="1.7" /><path d={path(c.anchors)} fill="none" stroke={c.color} strokeWidth={explainedHormone === i ? '3' : '2.1'} clipPath={`url(#${id})`} /></g>)}
      {approximate ? <rect x={x(start)} y="20" width={Math.max(3,x(end)-x(start))} height="119" fill="currentColor" opacity=".08" /> : null}
      <line x1={x(exploring)} x2={x(exploring)} y1="17" y2="139" stroke="currentColor" opacity=".5" strokeDasharray="2 4" />
    </svg>
    </div>
    <div className={styles.weekExplorer}>
      <label htmlFor={`${id}-week`} className={styles.srOnly}>Explore a pregnancy week</label>
      <input id={`${id}-week`} aria-valuetext={`Exploring week ${selected}. Your onboarding timeline is unchanged.`} type="range" min="1" max="40" value={selected} onChange={event=>setSelected(Number(event.target.value))} />
      <div className={styles.weekScale}>{scaleWeeks.map(w=><span key={w} style={{left:`${(w-1)/39*100}%`}}>{w===40?'40+':w}</span>)}{!approximate ? <button type="button" className={styles.timelineWeek} aria-label={`Return to your onboarding week ${start}`} style={{left:`${(Math.min(40,start)-1)/39*100}%`}} onClick={()=>{setHover(null);setSelected(Math.min(40,start));}}>{start}</button> : null}</div>
    </div>
    <details className={styles.hormoneGuide}><summary>A quick guide to your hormones <span>5 short explanations</span></summary><div>{education.map(h=><section key={h.name}><b>{h.name}</b><p>{h.body}</p></section>)}</div><small>Exploring the chart does not change your dashboard week.</small></details>
  </section>;
}

export function HormoneCaption(){return <p className={styles.hormoneCaption}>Illustrative patterns—not your hormone levels or a mood prediction. Separate relative scales; not lab measurements. <a href="https://www.ncbi.nlm.nih.gov/books/NBK278962/" target="_blank" rel="noopener noreferrer">Source ↗</a></p>;}
