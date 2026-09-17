"use client";

import { useEffect, useState, type CSSProperties } from "react";
import {
  Activity, ArrowLeft, ArrowRight, Baby, Check, Flower2, Heart, MessageCircle, MoveUpRight, Salad, ShieldCheck, Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { mayaApi, type JourneyOverview, type OnboardingPayload, type OnboardingResult } from "@/lib/maya-api";
import { Brand, StatusPanel } from "./visuals";

const diets = ["Vegetarian", "Vegan", "Non-vegetarian", "Egg-friendly", "Dairy-free", "Gluten-free"];
const symptoms = ["Back ache", "Heartburn", "Low energy", "Trouble sleeping"];
const allergies = ["Peanut", "Dairy", "Soy", "Gluten"];

export function Landing({
  start,
  chat,
  busy,
  error,
  retry,
}: {
  start: () => void;
  chat: () => void;
  busy: boolean;
  error: string;
  retry: () => void;
}) {

  return <main className="landing">
    <nav className="landing-nav"><Brand /><div><button className="landing-maya" onClick={chat}><MessageCircle /><b>Ask Maya</b></button></div></nav>
    <section className="hero">
      <div className="hero-copy">
        <span className="kicker"><Sparkles /> Thoughtful care, week by week</span>
        <h1><span>Feel held through</span><span>every <em>little change.</em></span></h1>
        <p>Bring your journey, preferences and questions into one calm space. Maya shows what is available now and stays clear about what still needs review.</p>
        <div className="hero-actions"><Button onClick={start} disabled={busy}>{busy ? "Opening…" : "Begin my journey"} <ArrowRight /></Button></div>
        <div className="trust"><div><span>K</span><span>A</span></div><p><b>Designed for the in-between moments</b><small>Guidance, never judgement.</small></p></div>
        {error ? <StatusPanel tone="error" title="Maya could not connect" message={error} action={retry} actionLabel="Retry" /> : null}
      </div>
      <div className="hero-art" aria-label="Maya care illustration">
        <div className="orbital o1"><span /><span /><span /><span /><span /></div><div className="orbital o2"><span /><span /><span /></div>
        <div className="orbit-center"><Flower2 /><span>care around you</span></div>
        <div className="orbit-tab tab-a"><Heart /><p><b>Safety first</b>Urgent concerns stop ordinary responses.</p></div>
        <div className="orbit-tab tab-b"><Baby /><p><b>Journey-aware</b>Your timeline shapes your space.</p></div>
        <div className="orbit-tab tab-c"><Salad /><p><b>Nourishment</b>Made for your preferences.</p></div>
        <div className="orbit-tab tab-d"><MessageCircle /><p><b>Ask Maya</b>A calm place to begin.</p></div>
      </div>
    </section>
    <section className="inside" id="inside"><p>A companion for</p><div><span><Heart /> wellbeing</span><span><Salad /> nourishment</span><span><Activity /> movement</span><span><MessageCircle /> questions</span></div></section>
    <section className="care" id="care"><div><span>01 / YOUR RHYTHM</span><h2>Less information.<br /><em>More relevance.</em></h2></div><div><p>Begin with your own week or postpartum timeline. Maya uses what you enter during onboarding—no sample week is selected for you.</p><button className="sample-link" onClick={start} disabled={busy}>Begin my journey <MoveUpRight /></button></div></section>
  </main>;
}

export function Onboarding({
  back,
  done,
  initialError = "",
  initialValues,
}: {
  back: () => void;
  done: (payload: OnboardingPayload) => Promise<OnboardingResult>;
  initialError?: string;
  initialValues?: OnboardingPayload | null;
}) {
  const [step, setStep] = useState(0);
  const [name, setName] = useState(initialValues?.name ?? "");
  const [journey, setJourney] = useState<"pregnant" | "postpartum">(initialValues?.journey ?? "pregnant");
  const [timelineMode, setTimelineMode] = useState<"due" | "week" | "month">(
    initialValues?.timeline_mode === "due" || initialValues?.timeline_mode === "month"
      ? initialValues.timeline_mode : "week"
  );
  const [timelineValue, setTimelineValue] = useState(initialValues?.timeline_value ?? "");
  const [diet, setDiet] = useState<string[]>(initialValues?.diets ?? []);
  const [feeling, setFeeling] = useState<string[]>(initialValues?.symptoms.filter(item => symptoms.includes(item)) ?? []);
  const [otherSymptom, setOtherSymptom] = useState(initialValues?.symptoms.find(item => !symptoms.includes(item)) ?? "");
  const [allergy, setAllergy] = useState<string[]>(initialValues?.allergies.filter(item => allergies.includes(item)) ?? []);
  const [otherAllergy, setOtherAllergy] = useState(initialValues?.allergies.find(item => !allergies.includes(item)) ?? "");
  const [restrictions, setRestrictions] = useState(initialValues?.restrictions?.join("; ") ?? "");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(initialError);
  const [safetyResult, setSafetyResult] = useState<OnboardingResult | null>(null);
  const timelineKey = JSON.stringify([journey, timelineMode, timelineValue]);
  const [timelineResult, setTimelineResult] = useState<{
    key: string; preview: JourneyOverview | null; error: string;
  } | null>(null);
  // Match results to inputs so a changed timeline never displays stale data.
  const timelinePreview = timelineResult?.key === timelineKey ? timelineResult.preview : null;
  const timelineError = timelineResult?.key === timelineKey ? timelineResult.error : "";
  const timelinePending = !!timelineValue && timelineResult?.key !== timelineKey;
  const titles = ["Let’s start with you", "Where are you in your journey?", "Your little timeline", "Make Maya feel like yours"];
  const toggle = (item: string, list: string[], set: (x: string[]) => void) => set(list.includes(item) ? list.filter(value => value !== item) : [...list, item]);
  const toggleDiet = (item: string) => setDiet(current => {
    if (current.includes(item)) return current.filter(value => value !== item);
    const base = ["Vegetarian", "Vegan", "Non-vegetarian"];
    const next = base.includes(item) ? current.filter(value => !base.includes(value) && !(item === "Vegan" && value === "Egg-friendly")) : current.filter(value => !(item === "Egg-friendly" && value === "Vegan"));
    return [...next, item];
  });

  useEffect(() => {
    let current = true;
    if (!timelineValue) return;
    const timer = setTimeout(() => {
      void mayaApi.previewTimeline({ journey, timeline_mode: journey === "postpartum" ? "birth_date" : timelineMode, timeline_value: timelineValue })
        .then(value => { if (current) setTimelineResult({ key: timelineKey, preview: value, error: "" }); })
        .catch(reason => { if (current) setTimelineResult({ key: timelineKey, preview: null, error: reason instanceof Error ? reason.message : "Check your timeline." }); });
    }, 200);
    return () => { current = false; clearTimeout(timer); };
  }, [journey, timelineMode, timelineValue, timelineKey]);

  const timelineHint = () => {
    if (!timelineValue) return null;
    if (journey === "postpartum") return "Maya will resolve your supported postpartum week from this date.";
    if (timelineMode === "month") return `Month ${timelineValue} will remain an approximate week range. Maya will not guess a single week.`;
    if (timelineMode === "due") return "Maya will calculate the exact journey week from this due date.";
    return `Maya will use pregnancy week ${timelineValue}.`;
  };

  const submit = async () => {
    if (!timelineValue) {
      setSubmitError("Please add your week, month, due date, or birth date so Maya can resolve your timeline safely.");
      return;
    }
    setSubmitting(true);
    setSubmitError("");
    setSafetyResult(null);
    try {
      const result = await done({
        name: name.trim(),
        journey,
        timeline_mode: journey === "postpartum" ? "birth_date" : timelineMode,
        timeline_value: timelineValue,
        diets: diet,
        allergies: [...allergy, ...(otherAllergy.trim() ? [otherAllergy.trim()] : [])],
        symptoms: [...feeling, ...(otherSymptom.trim() ? [otherSymptom.trim()] : [])],
        restrictions: restrictions.trim() ? [restrictions.trim()] : [],
        use_fictional_sample_record: false,
      });
      if (result.safety_blocked) setSafetyResult(result);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "Maya could not complete onboarding.");
    } finally {
      setSubmitting(false);
    }
  };

  const advance = () => {
    if (step === 3) {
      void submit();
      return;
    }
    if (step === 2 && (!timelineValue || (journey === "pregnant" && timelineMode === "week" && (!Number.isInteger(Number(timelineValue)) || Number(timelineValue) < 1 || Number(timelineValue) > 41)))) {
      setSubmitError("Enter a pregnancy week from 1 to 41, or choose a valid date or month before continuing.");
      return;
    }
    setSubmitError("");
    setStep(step + 1);
  };

  return <main className="onboarding">
    <aside>
      <Brand light onClick={back} />
      <div className="aside-copy"><span>YOUR SPACE, YOUR PACE</span><h2>Care should feel<br /><em>personal.</em></h2><p>A few details help Maya surface what matters now—and quietly leave the rest aside.</p></div>
      <div className="flower"><i /><i /><i /><i /><span /></div>
    </aside>
    <section className="onboard-main">
      <header><button onClick={step ? () => { setSubmitError(""); setStep(step - 1); } : back}><ArrowLeft /> Back</button><div className="onboard-meta"><span>0{step + 1} <i /> 04</span></div></header>
      <Progress value={(step + 1) * 25} />
      <p className="onboarding-boundary"><ShieldCheck /> Your choices shape your dashboard. Refreshing starts a new session.</p>
      <div className="onboard-content" key={step}>
        <span>A little about you</span><h1>{titles[step]}</h1>
        {step === 0 ? <div className="field name-field"><label htmlFor="name">What should we call you? <small>(optional)</small></label><Input id="name" aria-describedby="name-help" value={name} onChange={event => setName(event.target.value)} autoFocus /><p id="name-help">You can continue without adding a name.</p></div> : null}
        {step === 1 ? <RadioGroup value={journey} onValueChange={value => { setJourney(value as "pregnant" | "postpartum"); setTimelineValue(""); }} className="journey-list">
          {[
            { v: "pregnant", icon: Baby, t: "I’m pregnant", d: "Explore weekly growth, nutrition, movement and wellbeing." },
            { v: "postpartum", icon: Heart, t: "I’m postpartum", d: "Explore recovery, feeding, nourishment and wellbeing." },
          ].map(({ v, icon: Icon, t, d }) => <label key={v} className={journey === v ? "selected" : ""}><RadioGroupItem value={v} /><i><Icon /></i><p><b>{t}</b><small>{d}</small></p><Check /></label>)}
        </RadioGroup> : null}
        {step === 2 ? <div className="timeline-field">
          {journey === "postpartum" ? <>
            <label htmlFor="birth-date">When was your baby born?</label>
            <Input id="birth-date" type="date" value={timelineValue} onChange={event => setTimelineValue(event.target.value)} />
          </> : <>
            <label>How would you like to add your timeline?</label>
            <div className="timeline-modes">{([["week", "Current week"], ["month", "Current month"], ["due", "Due date"]] as const).map(([value, label]) => <button type="button" key={value} className={timelineMode === value ? "active" : ""} onClick={() => { setTimelineMode(value); setTimelineValue(""); }}>{label}</button>)}</div>
            <Input
              aria-label={timelineMode === "due" ? "Estimated due date" : timelineMode === "week" ? "Current pregnancy week" : "Current pregnancy month"}
              type={timelineMode === "due" ? "date" : "number"}
              min="1"
              max={timelineMode === "week" ? "41" : "9"}
              placeholder={timelineMode === "week" ? "e.g. 26" : timelineMode === "month" ? "e.g. 6" : undefined}
              value={timelineValue}
              onChange={event => setTimelineValue(event.target.value)}
            />
          </>}
          {timelinePreview ? <article className="timeline-reveal range-reveal"><div className="date-ring" style={{ "--timeline-progress": `${timelinePreview.progress_end}%` } as CSSProperties}><span><b>{timelinePreview.range ? `${timelinePreview.start}–${timelinePreview.end}` : timelinePreview.start}</b><small>{journey === "postpartum" ? "recovery week" : timelinePreview.range ? "week range" : "of 40 weeks"}</small></span></div><div><span>YOUR TIMELINE</span><h3>{timelinePreview.phase}</h3><p>{timelinePreview.label}</p><p>{timelineHint()}</p></div></article> : null}
          {timelinePending ? <p role="status">Calculating your timeline…</p> : null}
          {timelineError ? <p role="alert">{timelineError}</p> : null}
        </div> : null}
        {step === 3 ? <div className="preferences">
          <div><label>Food preferences <small>(optional)</small></label><div className="chips">{diets.map(item => <label key={item} className={diet.includes(item) ? "selected" : ""}><Checkbox checked={diet.includes(item)} onCheckedChange={() => toggleDiet(item)} />{item}</label>)}</div></div>
          <div><label>Food allergies or ingredients to avoid <small>(optional)</small></label><div className="chips">{allergies.map(item => <label key={item} className={allergy.includes(item) ? "selected" : ""}><Checkbox checked={allergy.includes(item)} onCheckedChange={() => toggle(item, allergy, setAllergy)} />{item}</label>)}</div><Input aria-label="Other allergy" value={otherAllergy} onChange={event => setOtherAllergy(event.target.value)} placeholder="Add another ingredient to avoid (optional)" /></div>
          <div><label>Symptoms you’re noticing <small>(optional; checked before continuing)</small></label><div className="chips">{symptoms.map(item => <label key={item} className={feeling.includes(item) ? "selected" : ""}><Checkbox checked={feeling.includes(item)} onCheckedChange={() => toggle(item, feeling, setFeeling)} />{item}</label>)}</div><Input aria-label="Other symptom" value={otherSymptom} onChange={event => setOtherSymptom(event.target.value)} placeholder="Describe another symptom (optional)" /></div>
        </div> : null}
        {submitError ? <StatusPanel tone="error" title="Please check this step" message={submitError} action={step === 3 ? () => void submit() : undefined} actionLabel={step === 3 ? "Retry" : undefined} /> : null}
        {safetyResult ? <StatusPanel
          tone="safety"
          title={safetyResult.symptom_checks.some(item => item.route === "urgent") ? "Please act on this now" : "Maya needs one safety detail first"}
          message={safetyResult.symptom_checks.filter(item => !item.ordinary_generation_allowed).map(item => item.message).join(" ")}
        /> : null}
        {safetyResult ? <button type="button" className="edit-symptoms" onClick={() => { setSafetyResult(null); setStep(3); }}>Back to symptoms <ArrowRight /></button> : null}
      </div>
      {step === 3 ? <div className="onboard-review"><label htmlFor="activity-restrictions">Activity restrictions or clinician instructions (optional)</label><Input id="activity-restrictions" value={restrictions} onChange={event => setRestrictions(event.target.value)} placeholder="Only instructions you have actually been given" /><p><b>Ready to open:</b> {timelinePreview?.label || timelineHint()}. {diet.length ? `Food preferences: ${diet.join(", ")}. ` : "No food preference selected. "}Your selected allergies and symptoms will remain in context. Use Back to change your timeline.</p></div> : null}
      <footer>
        <span>{step === 3 ? "No document is required." : ""}</span>
        <Button disabled={submitting || (step === 2 && (!timelinePreview || timelinePending)) || (step === 3 && !!safetyResult)} onClick={advance}>{submitting ? "Opening your dashboard…" : step === 3 && safetyResult ? "Review safety message" : step === 3 ? "Open my dashboard" : "Continue"} <ArrowRight /></Button>
      </footer>
    </section>
  </main>;
}
