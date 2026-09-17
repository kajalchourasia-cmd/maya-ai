"use client";

import { Activity, ArrowRight, Baby, Salad, Sparkles, Heart, Leaf, ShieldCheck, Droplets } from "lucide-react";
import type { DashboardGuidance, GuidanceSection, HomeData, StaticFact } from "@/lib/maya-api";
import styles from "./weekly-guidance.module.css";
import { JourneyHormones, HormoneCaption } from "./journey-hormones";

export function FactNote({ fact, label }: { fact: StaticFact; label: string }) {
  return <section className={styles.fact} aria-label={label}>
    <span className={styles.factLabel}><Sparkles aria-hidden="true" />{label}</span><h3>{fact.title}</h3><p>{fact.body}</p>
    <details className={`${styles.sources} ${styles.factSource}`}><summary>Source</summary>{fact.source_links.map(source => <a key={source.id} href={source.url} target="_blank" rel="noopener noreferrer">{source.title} ↗</a>)}</details>
  </section>;
}

export function GuidanceSections({ sections }: { sections: GuidanceSection[] }) {
  return <div className={styles.grid}>{sections.map(section => {
    const Icon = /water|hydrat/.test(section.id) ? Droplets : /safety|avoid|restriction/.test(section.id) ? ShieldCheck : /strength|aerobic|mobility|pelvic|movement/.test(section.id) ? Activity : /symptom|heartburn|comfort|support|wellbeing/.test(section.id) ? Heart : section.food_options.length ? Salad : Leaf;
    return <article id={`guidance-${section.id}`} key={section.id} className={`${styles.card} ${section.tone === "context" ? styles.context : ""}`}>
    <header className={styles.guidanceHeading}><i><Icon aria-hidden="true" /></i><h3>{section.title}</h3></header>
    {section.reference ? <div className={styles.reference}>{section.reference}<small>{section.id === "aerobic" ? "weekly activity reference" : "daily intake reference"}</small></div> : null}
    <p>{section.summary}</p>
    {section.food_options.length ? <div className={styles.foods}><h4>Food options for your preferences</h4><ul>{section.food_options.map(food => <li key={food.id}>{food.label}</li>)}</ul></div> : null}
    {section.bullets.length ? <ul className={styles.points}>{section.bullets.map(point => <li key={point}>{point}</li>)}</ul> : null}
    {section.basis ? <p className={styles.basis}>{section.basis}</p> : null}
    <details className={styles.sources}><summary>Sources & details</summary><ul>{section.source_links.map(source => <li key={source.id}><a href={source.url} target="_blank" rel="noopener noreferrer">{source.title} ↗</a><small>{source.locator} · {source.jurisdiction}</small></li>)}</ul></details>
  </article>;})}</div>;
}

export function NutritionReferenceStrip({ sections }: { sections: GuidanceSection[] }) {
  const labels: Record<string,string> = {protein:'Protein',iron:'Iron',calcium:'Calcium',folate:'Folate',hydration:'Water','postpartum-calcium':'Calcium'};
  const items = Object.keys(labels).flatMap(id => {
    const section = sections.find(s=>s.id===id);
    if (!section) return [];
    // Reuse the existing source-linked hydration text; never insert a target
    // when restrictions have removed it from the backend's guidance.
    const water = id === 'hydration' ? section.bullets.join(' ').match(/\b\d+[–-]\d+ US cups/)?.[0] : undefined;
    const value = section.reference || (water ? `${water} / day` : null);
    if (!value && id !== 'hydration') return [];
    return [{section,label:labels[id],value:value || 'Follow your care guidance'}];
  });
  if (!items.length) return null;
  return <section className={styles.nutrientSummary} aria-label="Daily nutrition references">
    <header><b>Daily nourishment, at a glance</b><span>References, not an intake tracker</span></header>
    <div className={styles.nutrientRail} tabIndex={0} aria-label="Nutrient references; scroll for more">
      {items.map(({section,label,value})=><a key={section.id} href={`#guidance-${section.id}`}><i>{section.id==='hydration' ? <Droplets aria-hidden="true" /> : <Leaf aria-hidden="true" />}</i><span>{label}</span><strong>{value}</strong><small>View guidance & source →</small></a>)}
    </div>
    <p>General references—not personalised prescriptions. Age, stage and your care team’s advice matter.</p>
  </section>;
}

export function NutritionGuidance({ guidance }: { guidance: DashboardGuidance }) {
  const personal = guidance.nutrition.filter(s => s.tone === 'context' || s.id === 'stage-nutrition');
  const routines = guidance.nutrition.filter(s => ['supplements','food-safety'].includes(s.id));
  const daily = guidance.nutrition.filter(s => !personal.includes(s) && !routines.includes(s));
  const groups = [
    {id:'personal',title:'Shaped around you',description:'Your stage, preferences and reported symptoms come first.',sections:personal},
    {id:'daily',title:'Your everyday nourishment',description:'Food choices and daily references, together in one place.',sections:daily},
    {id:'routine',title:'Supplements & food safety',description:'Keep your existing care routine separate from everyday food choices.',sections:routines},
  ];
  return <>
    <NutritionReferenceStrip sections={guidance.nutrition} />
    <p className={styles.referenceNote}>{guidance.reference_note}</p>
    {guidance.unmatched_allergies.length ? <div className={styles.notice}>Maya could not reliably match these ingredients: <b>{guidance.unmatched_allergies.join(", ")}</b>. Nutrient information is shown below; individual food suggestions are held until these ingredients can be checked. You can edit your details to use an ingredient name.</div> : null}
    {groups.filter(g=>g.sections.length).map(group=><section className={styles.nutritionGroup} key={group.id} aria-label={group.title}><header><h3>{group.title}</h3><p>{group.description}</p></header><GuidanceSections sections={group.sections} /></section>)}
    <p className={styles.footnote}>{guidance.food_note}</p>
  </>;
}

export function DashboardMetrics({ home, editDetails }: { home: HomeData; editDetails: () => void }) {
  const guidance = home.dashboard_guidance;
  const overview = guidance.journey;
  const postpartum = home.journey.stage === "postpartum";
  const content = guidance.overview_content;
  return <section className={styles.metrics} aria-label="Your journey overview">
    <article><Baby /><span>YOUR JOURNEY</span><h2>{overview.range ? `Weeks ${overview.start}–${overview.end}` : `Week ${overview.start}`}</h2><b>{overview.phase}</b><p>{overview.range ? "Based on the month you entered" : postpartum ? "Based on your delivery date" : "Based on your onboarding timeline"}</p><button type="button" onClick={editDetails}>Edit my details <ArrowRight /></button></article>
    <article><Salad /><span>NUTRITION FOCUS</span><h2>{guidance.nutrition_focus}</h2><p>{guidance.nutrition_focus_detail}</p><button onClick={() => window.dispatchEvent(new CustomEvent("maya-open-tab", {detail:"nutrition"}))}>Explore nutrition <ArrowRight /></button></article>
    <article><Sparkles /><span>ENERGY FOCUS</span><h2>{content.energy.title}</h2><p>{content.energy.body}</p><details className={styles.sources}><summary>Why this focus?</summary><p>A supportive suggestion, not a prediction of how you feel.</p>{content.energy.source_links.map(s => <a key={s.id} href={s.url} target="_blank" rel="noopener noreferrer">{s.title} ↗</a>)}</details></article>
    <article><Activity /><span>MOVEMENT FOCUS</span><h2>{guidance.movement_focus}</h2><p>{guidance.movement_focus_detail}</p><button onClick={() => window.dispatchEvent(new CustomEvent("maya-open-tab", {detail:"movement"}))}>Explore movement <ArrowRight /></button></article>
  </section>;
}

export function JourneyProgress({ home }: { home: HomeData }) {
  const overview = home.dashboard_guidance.journey;
  const postpartum = home.journey.stage === "postpartum";
  if (!postpartum) {
    return <article className={`trimester ${styles.pregnancyJourney}`} aria-label="Your pregnancy journey">
      <JourneyHormones key={`${overview.start}-${overview.end}`} start={overview.start} end={overview.end} approximate={overview.range} />
      {home.dashboard_guidance.overview_content?.maternal_fact ? <FactNote fact={home.dashboard_guidance.overview_content.maternal_fact} label="A LITTLE ABOUT YOU" /> : null}
      <HormoneCaption />
    </article>;
  }
  return <article className={`trimester ${styles.journey}`}>
    <header><div><span>YOUR JOURNEY</span><h2>{overview.phase}</h2></div><i><Baby /></i></header>
    <div className={styles.progressTrack} role="img" aria-label={`${overview.label}. ${overview.progress_label}`}>
      <span style={{ width: `${overview.progress_start}%` }} />
      {overview.range ? <i style={{ left: `${overview.progress_start}%`, width: `${overview.progress_end - overview.progress_start}%` }} /> : null}
    </div>
    <div className={styles.progressLabels}>{(postpartum ? ["Birth", "Week 6", "Week 12"] : ["First trimester", "Second trimester", "Third trimester"]).map(label => <span key={label}>{label}</span>)}</div>
    <p>{overview.label}. {overview.range ? "The shaded part shows your approximate range." : postpartum ? "Recovery happens at your own pace." : "Your food and movement guidance follows this stage."}</p>
    <small>{overview.progress_label}</small>
    {home.dashboard_guidance.overview_content?.maternal_fact ? <FactNote fact={home.dashboard_guidance.overview_content.maternal_fact} label="A LITTLE ABOUT YOU" /> : null}
  </article>;
}
