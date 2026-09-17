import { Activity, ArrowRight, Heart, Salad, ShieldCheck, Sparkles } from "lucide-react";
import type { HomeData } from "@/lib/maya-api";

export function WeekHighlights({home, openTab, buildPlan, hasPlan}: {home:HomeData;openTab:(tab:string)=>void;buildPlan:()=>void;hasPlan:boolean}) {
  const guidance = home.dashboard_guidance;
  const symptom = guidance.symptoms.find(s=>s.id!=='reported-symptoms' && s.id!=='symptom-notes' && s.id!=='urgent-signs') || guidance.symptoms[0];
  const highlights = [
    {id:'nutrition',label:'Nutrition',title:guidance.nutrition_focus,body:guidance.nutrition.find(s=>s.id==='stage-nutrition')?.summary || guidance.nutrition_focus_detail,Icon:Salad},
    {id:'movement',label:'Movement',title:guidance.movement_focus,body:guidance.movement_focus_detail,Icon:Activity},
    {id:'symptoms',label:'Symptoms',title:home.confirmed_context.symptoms.length ? home.confirmed_context.symptoms.join(', ') : 'Check in with your body',body:symptom?.summary || 'No symptoms reported. Explore what to watch for and when to seek support.',Icon:ShieldCheck},
    {id:'wellbeing',label:'Self-love',title:guidance.overview_content.energy.title,body:guidance.overview_content.energy.body,Icon:Heart},
  ];
  return <div className="week-highlights">
    <div className="week-highlight-grid">{highlights.map(({id,label,title,body,Icon})=><article key={id} data-category={id}><span><Icon aria-hidden="true" />{label}</span><h3>{title}</h3><p>{body}</p><button onClick={()=>openTab(id)}>Explore {label.toLowerCase()} <ArrowRight aria-hidden="true" /></button></article>)}</div>
    <section className="week-plan-invitation"><div><span><Sparkles aria-hidden="true" /> MAKE ROOM FOR YOUR WEEK</span><h3>A little structure, on your terms.</h3><p>Bring nourishment, movement and self-care into one Monday–Sunday view, using your current preferences.</p></div><button onClick={buildPlan}>{hasPlan ? 'Rebuild my weekly plan' : 'Create my weekly plan'} <ArrowRight aria-hidden="true" /></button></section>
  </div>;
}
