import type { PlanResponse, GuidanceSection } from "@/lib/maya-api";

const weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
type Item = NonNullable<PlanResponse["schedule"]>["items"][number];
const labelFor = (item: Item) => item.slot || item.start || (item.domain === "wellbeing" ? "Self-love" : item.domain[0].toUpperCase()+item.domain.slice(1));
const mealSuffix = '. Add a suitable starchy food and vegetables or fruit to make a varied meal; check all ingredients.';
function mealOptions(item: Item): string[] | null {
  const prefix = 'Choose a protein component: ';
  return item.origin === 'source_linked_catalogue' && item.item.startsWith(prefix) && item.item.endsWith(mealSuffix)
    ? item.item.slice(prefix.length,-mealSuffix.length).split(' OR ') : null;
}
function ScheduleItem({item}: {item:Item}) {
  const options=mealOptions(item);
  return options ? <div className="meal-options"><small>CHOOSE ONE</small><ul>{options.map((option,index)=><li key={index}>{option}</li>)}</ul></div> : <p>{item.item}</p>;
}

export function WeeklySchedule({ schedule, nutritionReferences = [] }: { schedule: NonNullable<PlanResponse["schedule"]>; nutritionReferences?: GuidanceSection[] }) {
  const days = Array.from(new Set(schedule.items.map(item => item.day))).sort((a,b)=>Number(a)-Number(b));
  const authored = schedule.items.filter(item => item.origin === 'source_linked_catalogue');
  const dailyItems = authored.length ? authored : schedule.items;
  const evidence = Array.from(new Map(schedule.items.filter(item => !item.origin).map(item => [item.item, item])).values());
  // Move identical reminders below the grid only when present on every day.
  const labels = Array.from(new Set(dailyItems.map(labelFor)));
  const shared = days.length > 1 ? labels.filter(label => !['Breakfast','Lunch','Dinner'].includes(label) && days.every(day => dailyItems.filter(i=>i.day===day && labelFor(i)===label).length===1) && new Set(dailyItems.filter(i=>labelFor(i)===label).map(i=>i.item)).size===1) : [];
  const columns = labels.filter(label=>!shared.includes(label));
  const cell = (day: string, label: string) => dailyItems.filter(i=>i.day===day && labelFor(i)===label);
  const references = schedule.items.some(i=>i.domain==='nutrition') ? nutritionReferences.filter(s=>s.reference && ['protein','iron','calcium','folate','postpartum-calcium'].includes(s.id)) : [];
  return <section className="weekly-schedule" aria-label="Your weekly schedule">
    {references.length ? <section className="plan-nutrient-guide" aria-label="Daily nutrition references"><header><h4>Daily nutrition references</h4><span>Reference, not your menu&apos;s calculated intake</span></header><div>{references.map(s=><article key={s.id}><span>{s.title}</span><b>{s.reference}</b><details><summary>Basis & source</summary><p>{s.basis}</p>{s.source_links.map(source=><a key={source.id} href={source.url} target="_blank" rel="noopener noreferrer">{source.title} ↗</a>)}</details></article>)}</div><p><b>Menu totals: not calculated.</b> Portions and nutrient composition are not recorded for these choices. These references do not prove that the menu meets your needs; choosing a meal is not a record of food eaten.</p></section> : null}
    {dailyItems.some(item=>mealOptions(item)) ? <p className="schedule-meal-note">Choose one protein component at each meal. Add a suitable starchy food and vegetables or fruit to make a varied meal; check all ingredients.</p> : null}
    {columns.length ? <>
      <div className="schedule-table-wrap" tabIndex={0} role="region" aria-label="Compare your days; scroll horizontally if needed">
        <table className="schedule-table"><caption>{days.length===1 ? 'Your one-day outline' : 'At a glance · Monday to Sunday'}</caption>
          <thead><tr><th scope="col">Day</th>{columns.map(label=><th key={label} scope="col">{label}</th>)}</tr></thead>
          <tbody>{days.map(day=><tr key={day}><th scope="row">{days.length===1 ? 'Your day' : weekdays[Number(day)-1] || day}</th>{columns.map(label=><td key={label}>{cell(day,label).length ? cell(day,label).map(item=><ScheduleItem key={item.schedule_item_id} item={item} />) : <span className="schedule-unassigned">Not scheduled</span>}</td>)}</tr>)}</tbody>
        </table>
      </div>
      <div className="schedule-mobile">{days.map(day=><article key={day}><h4>{days.length===1 ? 'Your day' : weekdays[Number(day)-1] || day}</h4>{columns.map(label=><section key={label}><b>{label}</b>{cell(day,label).length ? cell(day,label).map(item=><ScheduleItem key={item.schedule_item_id} item={item} />) : <p>Not scheduled</p>}</section>)}</article>)}</div>
    </> : <p className="schedule-repeat-note">The guidance below applies each day, Monday–Sunday.</p>}
    {shared.length ? <section className="schedule-everyday" aria-label="Every day of your week"><h4>Every day of your week</h4><div>{shared.map(label=>{const item = dailyItems.find(i=>labelFor(i)===label)!;return <article key={label}><b>{label}</b><p>{item.item}</p></article>;})}</div></section> : null}
    {authored.length && evidence.length ? <details className="plan-evidence"><summary>Guidance retrieved for your plan</summary>{evidence.map(item => <p key={item.schedule_item_id}>{item.item}</p>)}</details> : null}
  </section>;
}
