"use client";

import { useContext, useEffect, useMemo, useRef, useState } from "react";
import type { LucideIcon } from "lucide-react";
import {
  Activity, ArrowLeft, ArrowRight, Baby, CalendarDays, ChevronRight,
  FileHeart, Flower2, Heart, Info, Menu, MoonStar, MoveUpRight,
  Salad, ShieldCheck, Sparkles, SunMedium,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { GovernedCard, HomeData, PlanResponse } from "@/lib/maya-api";
import { getBabyGrowth } from "../baby-growth-library";
import { getGrowthMeasurements } from "../growth-measurements";
import { BalancedGrowthImage, Brand, PreviewFooter, StatusPanel } from "./visuals";
import growthStyles from "./growth-card.module.css";
import { DashboardMetrics, FactNote, GuidanceSections, JourneyProgress, NutritionGuidance } from "./weekly-guidance";
import { WeeklySchedule } from "./weekly-schedule";
import { LatestPlanContext } from "./plan-context";
import { WeekHighlights } from "./week-highlights";
import "./plan-layout.css";

type Focus = "balanced" | "nutrition" | "movement" | "wellbeing";
const iconByDomain: Record<string, LucideIcon> = {
  health: Heart,
  nutrition: Salad,
  movement: Activity,
  symptoms: ShieldCheck,
  wellbeing: MoonStar,
  preparation: CalendarDays,
  recovery: Heart,
  feeding: Baby,
  documents: FileHeart,
};

function contextText(values: string[], empty: string) {
  return values.length ? values.join(", ") : empty;
}

function GovernedCards({
  cards,
  action,
}: {
  cards: GovernedCard[];
  action: (card: GovernedCard) => void;
}) {
  return <div className="plan-cards governed-cards">
    {cards.map(card => {
      const Icon = iconByDomain[card.domain] || Sparkles;
      return <article className={card.display_allowed ? "green" : "unavailable-card"} key={card.card_id}>
        <i><Icon /></i>
        <div>
          <span>{card.journey_scope}</span>
          <h3>{card.title}</h3>
          <p>{card.summary}</p>
          <small><ShieldCheck /> {card.display_allowed ? "Reviewed for display" : "Awaiting specialist and release review"}</small>
          {card.source_links?.length ? <div className="card-source-links">{card.source_links.map(source => <a key={source.url} href={source.url} target="_blank" rel="noopener noreferrer">Source: {source.title} <MoveUpRight /></a>)}</div> : null}
          <button onClick={() => action(card)}>{card.suggested_action} <ChevronRight /></button>
        </div>
      </article>;
    })}
  </div>;
}

export function ConnectedPlan({
  runPlan,
  initialFocus = "balanced",
  autoBuild = false,
  onAutoBuildComplete,
  journeyLabel,
  nutritionReferences = [],
}: {
  runPlan: (focus: Focus) => Promise<PlanResponse>;
  initialFocus?: Focus;
  autoBuild?: boolean;
  onAutoBuildComplete?: () => void;
  journeyLabel?: string;
  nutritionReferences?: HomeData['dashboard_guidance']['nutrition'];
}) {
  const latestPlan = useContext(LatestPlanContext);
  const [focus, setFocus] = useState<Focus>(autoBuild ? initialFocus : latestPlan?.focus || initialFocus);
  const [result, setResult] = useState<PlanResponse | null>(latestPlan);
  const [loading, setLoading] = useState(autoBuild);
  const [error, setError] = useState("");
  const runPlanRef = useRef(runPlan);
  const completionRef = useRef(onAutoBuildComplete);
  const autoStarted = useRef(false);
  useEffect(() => {
    runPlanRef.current = runPlan;
    completionRef.current = onAutoBuildComplete;
  }, [runPlan, onAutoBuildComplete]);

  useEffect(() => {
    if (!autoBuild || autoStarted.current) return;
    autoStarted.current = true;
    void runPlanRef.current(initialFocus).then(setResult).catch(reason => {
      setError(reason instanceof Error ? reason.message : "The plan could not be created.");
    }).finally(() => {
      setLoading(false);
      completionRef.current?.();
    });
  }, [autoBuild, initialFocus]);

  const build = async () => {
    setLoading(true);
    setError("");
    try {
      setResult(await runPlan(focus));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The plan could not be created.");
    } finally {
      setLoading(false);
    }
  };

  return <section className="connected-plan" id="plan-builder">
    <header>
      <div><span>{journeyLabel || 'YOUR WEEK, YOUR WAY'}</span><h2>Your weekly plan</h2><p>A clear view of your days, shaped around your preferences.</p></div>
      <div className="plan-actions">
        <label htmlFor="plan-focus">Plan focus</label>
        <select id="plan-focus" value={focus} onChange={event => setFocus(event.target.value as Focus)}>
          <option value="balanced">Balanced week</option>
          <option value="nutrition">Nutrition</option>
          <option value="movement">Movement</option>
          <option value="wellbeing">Self-love</option>
        </select>
        <Button onClick={() => void build()} disabled={loading}>{loading ? "Building…" : result ? "Rebuild plan" : "Build weekly plan"} <Sparkles /></Button>
      </div>
    </header>
    {error ? <StatusPanel tone="error" title="Plan unavailable" message={error} action={() => void build()} actionLabel="Retry plan" /> : null}
    {!result && !loading && !error ? <p className="plan-empty">Choose a focus to create your Monday–Sunday schedule. It stays available during this session.</p> : null}
    {loading ? <div className="loading-state" role="status"><span /><p>Maya is checking safety, constraints and display validation…</p></div> : null}
    {result && !loading ? <div className="connected-result">
      {error ? <p>Your previous plan is shown below; it has not been updated.</p> : null}
      <h3 className="plan-result-label">{({balanced:'Balanced week',nutrition:'Nutrition',movement:'Movement',wellbeing:'Self-love'} as const)[result.focus || focus]} · {new Set(result.schedule?.items.map(i=>i.day)).size === 1 ? 'One-day outline' : 'Monday–Sunday'}</h3>
      <details className="plan-sources plan-method"><summary>How your plan was put together</summary><p>{result.display.summary}</p></details>
      {result.display.uncertainties.length ? <details className="plan-sources"><summary>Plan context</summary><p>{result.display.uncertainties.join(' ')}</p></details> : null}
      {result.display.applied_constraints.length ? <div className="constraint-strip"><b>Context applied</b><span>{result.display.applied_constraints.join(" · ")}</span></div> : null}
      {result.schedule?.items.length ? <WeeklySchedule schedule={result.schedule} nutritionReferences={nutritionReferences} /> : <StatusPanel tone="empty" title="No schedule was displayed" message={result.display.uncertainties.join(" ") || "Maya stopped before producing a schedule."} />}
      {result.display.citations.length ? <details className="plan-sources"><summary>Sources</summary>{result.display.citations.map(source => <a key={source.evidence_id} href={source.url} target="_blank" rel="noopener noreferrer">{source.source_title} ↗</a>)}</details> : null}
      <small><ShieldCheck /> Flexible guidance, not a prescribed treatment. Refreshing or editing your onboarding starts a new plan.</small>
    </div> : null}
  </section>;
}

function PregnancyComparison({
  home,
  openLibrary,
}: {
  home: HomeData;
  openLibrary: () => void;
}) {
  const preview = home.comparison_preview;
  if (preview.display_mode === "range_confirmation") {
    return <article className="baby-size empty" role="status">
      <header><span>YOUR SIZE STORY</span><button onClick={openLibrary}>EXPLORE ALL WEEKS <ArrowRight /></button></header>
      <StatusPanel
        title={`Pregnancy weeks ${preview.range_start}–${preview.range_end}`}
        message="A month gives an approximate range. Confirm an exact week before Maya shows one personalised comparison."
      />
    </article>;
  }
  if (!preview.eligible_context || preview.exact_week === null) {
    return <article className="baby-size empty" role="status">
      <header><span>YOUR SIZE STORY</span><button onClick={openLibrary}>EXPLORE ALL WEEKS <ArrowRight /></button></header>
      <StatusPanel title="Comparison unavailable" message="Confirm a supported pregnancy week to see an editorial Product Preview comparison." />
    </article>;
  }

  const item = getBabyGrowth(preview.exact_week);
  const measurements = getGrowthMeasurements(preview.exact_week);
  const hasComparison = preview.exact_week > 2 && Boolean(item.comparisonAsset || item.comparison);
  const article = /^[aeiou]/i.test(item.comparison) ? "an" : "a";
  return <article className={`baby-size ${growthStyles.card}`}>
    <header><span>GROWTH AT A GLANCE</span><span className={growthStyles.week}>Week {preview.exact_week}</span></header>
    {item.babyAsset && item.comparisonAsset ? <div className={growthStyles.pair}>
      <span><BalancedGrowthImage asset={item.babyAsset} label={`Baby illustration, week ${preview.exact_week}`} /></span>
      <span><BalancedGrowthImage asset={item.comparisonAsset} label={item.comparison} /></span>
    </div> : <p className={growthStyles.early}>{measurements?.earlyNote}</p>}
    <h2>{hasComparison ? <>This week, your baby is about the size of {article} <em>{item.comparison.toLowerCase()}.</em></> : <>Every little beginning<br /><em>has its own story.</em></>}</h2>
    {measurements?.length || measurements?.weight ? <dl className={growthStyles.measures}>
      <div><dt>Approx. length</dt><dd>{measurements.length || "Too early"}</dd></div>
      <div><dt>Approx. weight</dt><dd>{measurements.weight || "Too early"}</dd></div>
    </dl> : null}
    {home.dashboard_guidance.overview_content?.baby_fact ? <FactNote fact={home.dashboard_guidance.overview_content.baby_fact} label="A LITTLE ABOUT YOUR BABY" /> : null}
    <p className={growthStyles.note}><Info /><span>Visual estimates only; your scan is your baby’s individual reference.</span></p>
  </article>;
}

const pregnancyFaqs = [
  "What should I ask at my next visit?",
  "Can you explain what information is missing from my plan?",
  "Show meal options that respect my reported allergy",
  "Help me prepare a symptom timeline",
];
const postpartumFaqs = [
  "What should I ask about recovery at my next visit?",
  "Show easy nourishment options",
  "Help me prepare a feeding question",
  "Create a wellbeing support plan",
];

function ContentTabs({
  home,
  openChat,
  runPlan,
  postpartum = false,
}: {
  home: HomeData;
  openChat: (question?: string) => void;
  runPlan: (focus: Focus) => Promise<PlanResponse>;
  postpartum?: boolean;
}) {
  const [activeTab, setActiveTab] = useState(postpartum ? "recovery" : "health");
  const latestPlan = useContext(LatestPlanContext);
  useEffect(() => {
    const open = (event: Event) => {
      const tab = (event as CustomEvent).detail;
      if (tab === "nutrition" || tab === "movement") {
        setActiveTab(tab);
        document.getElementById("explore")?.scrollIntoView({behavior:"smooth"});
      }
    };
    window.addEventListener("maya-open-tab", open);
    return () => window.removeEventListener("maya-open-tab", open);
  }, []);
  const [requestedFocus, setRequestedFocus] = useState<Focus>("balanced");
  const [planRequestSequence, setPlanRequestSequence] = useState(0);
  const [pendingAutoBuild, setPendingAutoBuild] = useState(false);
  const tabs = postpartum
    ? [
        ["recovery", "Recovery"],
        ["nutrition", "Nourishment"],
        ["movement", "Movement"],
        ["feeding", "Feeding"],
        ["symptoms", "Symptoms"],
        ["wellbeing", "Self-love"],
        ["faq", "FAQs"],
        ["plans", "Plans"],
      ]
    : [
        ["health", "This week"],
        ["nutrition", "Nutrition"],
        ["movement", "Movement"],
        ["symptoms", "Symptoms"],
        ["wellbeing", "Self-love"],
        ["faq", "FAQs"],
        ["plans", "Plans"],
      ];
  const cardsFor = (domain: string) => home.content_cards.filter(card => card.domain === domain || (domain === "health" && card.domain === "preparation"));
  const buildFromHighlights = () => {
    setRequestedFocus('balanced');
    setPlanRequestSequence(sequence => sequence + 1);
    setPendingAutoBuild(true);
    setActiveTab('plans');
  };
  const cardAction = (card: GovernedCard) => {
    if (card.domain === "nutrition" || card.domain === "movement" || card.domain === "wellbeing") {
      setRequestedFocus(card.domain);
      setPlanRequestSequence(sequence => sequence + 1);
      setPendingAutoBuild(true);
      setActiveTab("plans");
      return;
    }
    openChat(card.suggested_action);
  };
  const faqs = postpartum ? postpartumFaqs : pregnancyFaqs;
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null);

  return <section className="plan" id="explore">
    <Tabs value={activeTab} onValueChange={setActiveTab}>
      <header className="plan-nav">
        <div><span>{postpartum ? "POSTPARTUM SPACE" : home.journey_label.toUpperCase()}</span><h2>Explore your Maya space.</h2></div>
        <TabsList aria-label="Dashboard sections">{tabs.map(([value, label]) => <TabsTrigger value={value} key={value}>{label}</TabsTrigger>)}</TabsList>
      </header>
      <div className={`plan-layout ${activeTab === 'plans' ? 'plan-layout-wide' : ''}`}><div>
        {tabs.filter(([value]) => !["faq", "plans", "documents"].includes(value)).map(([value, label], index) => <TabsContent value={value} key={value}>
          <Intro n={String(index + 1).padStart(2, "0")} title={value === "health" || value === "recovery" ? 'Your week, at a glance.' : label} text={`For ${home.journey_label.toLowerCase()}, with your preferences and reported symptoms in view.`} />
          {value === "nutrition" ? <NutritionGuidance guidance={home.dashboard_guidance} />
            : value === "movement" ? <GuidanceSections sections={home.dashboard_guidance.movement} />
            : value === "symptoms" ? <GuidanceSections sections={home.dashboard_guidance.symptoms} />
            : value === "wellbeing" ? <GuidanceSections sections={home.dashboard_guidance.wellbeing} />
            : value === "health" || value === "recovery" ? <WeekHighlights home={home} openTab={setActiveTab} buildPlan={buildFromHighlights} hasPlan={Boolean(latestPlan?.schedule?.items.length)} />
            : <GovernedCards cards={cardsFor(value)} action={cardAction} />}
        </TabsContent>)}
        <TabsContent value="faq"><Intro n="FAQ" title={home.dashboard_guidance.overview_content.faq_label} text="Open a question for a source-linked answer. Month labels are approximate; ask Maya for a personal follow-up." /><div className="faqs">{home.dashboard_guidance.overview_content.faqs.map(({ id, question, answer, source_links }, index) => <div className="faq-item" key={id}><button aria-expanded={expandedFaq === index} aria-controls={`faq-answer-${id}`} onClick={() => setExpandedFaq(expandedFaq === index ? null : index)}><span>{String(index + 1).padStart(2, "0")}</span>{question}<ChevronRight /></button>{expandedFaq === index ? <div id={`faq-answer-${id}`} className="faq-answer"><p>{answer}</p><div>{source_links.map(source => <a key={source.id} href={source.url} target="_blank" rel="noopener noreferrer">{source.title} ↗ </a>)}</div><button type="button" onClick={() => openChat(`Please explain this topic for my situation: ${question}`)}>Ask Maya a follow-up <ArrowRight /></button></div> : null}</div>)}</div></TabsContent>
        <TabsContent value="plans"><ConnectedPlan key={`${requestedFocus}-${planRequestSequence}`} journeyLabel={home.journey_label} nutritionReferences={home.dashboard_guidance.nutrition} runPlan={runPlan} initialFocus={requestedFocus} autoBuild={pendingAutoBuild} onAutoBuildComplete={() => setPendingAutoBuild(false)} /></TabsContent>
      </div>
      <aside>
        <article className="ask-card"><header><span><i><Flower2 /></i> ASK MAYA</span><button onClick={() => openChat()} aria-label="Open Ask Maya"><MoveUpRight /></button></header><div className="maya-signal"><i /><i /><i /><span><Sparkles /></span></div><h3>What’s on your mind?</h3><p className="maya-description">Ask in your own words. Maya keeps the timeline and preferences you entered in context.</p><p className="prompt-label">You could ask:</p><div className="quick-prompts">{faqs.slice(0, 3).map(question => <button key={question} onClick={() => openChat(question)}>{question}<ChevronRight /></button>)}</div><button className="open-maya" onClick={() => openChat()}>Talk with Maya <ArrowRight /></button></article>
        <article className="dos"><div className="dos-grid"><section><b className="do-title">YOUR CHOICES</b><p>{contextText(home.confirmed_context.diets, "No diet preference added")}</p><p>{home.journey_label}</p></section><section><b className="dont-title">CONSTRAINTS</b><p>{home.confirmed_context.allergies.length ? `Avoid: ${home.confirmed_context.allergies.join(", ")}` : "No ingredients to avoid reported"}</p><p>{home.confirmed_context.symptoms.length ? `Reported: ${home.confirmed_context.symptoms.join(", ")}` : "No symptoms reported"}</p></section></div></article>
      </aside></div>
    </Tabs>
    <PreviewFooter />
  </section>;
}

export function PregnancyDashboard({
  home,
  openChat,
  goHome,
  editDetails,
  openLibrary,
  runPlan,
}: {
  home: HomeData;
  openChat: (question?: string) => void;
  goHome: () => void;
  editDetails: () => void;
  openLibrary: () => void;
  runPlan: (focus: Focus) => Promise<PlanResponse>;
}) {
  return <main className="dashboard">
    <header className="dash-nav"><Brand onClick={goHome} /><div><button className="emergency-route" onClick={() => openChat("I need urgent help")}><ShieldCheck /> Get urgent help</button>{home.name ? <button className="profile" onClick={() => document.getElementById("explore")?.scrollIntoView({ behavior: "smooth" })} aria-label="Open your sample context"><i>{home.name[0]}</i><b>{home.name}</b></button> : null}<button className="mobile-menu" onClick={() => document.getElementById("explore")?.scrollIntoView({ behavior: "smooth" })} aria-label="Open dashboard sections"><Menu /></button></div></header>
    <DashboardMetrics home={home} editDetails={editDetails} />
    <section className="growth">
      <JourneyProgress home={home} />
      <PregnancyComparison home={home} openLibrary={openLibrary} />
    </section>
    <ContentTabs home={home} openChat={openChat} runPlan={runPlan} />
    <button className="floating-chat" onClick={() => openChat()}><i><Flower2 /></i><span><b>Ask Maya</b><small>Here with you</small></span></button>
  </main>;
}

export function PostpartumDashboard({
  home,
  openChat,
  goHome,
  editDetails,
  runPlan,
}: {
  home: HomeData;
  openChat: (question?: string) => void;
  goHome: () => void;
  editDetails: () => void;
  runPlan: (focus: Focus) => Promise<PlanResponse>;
}) {
  return <main className="dashboard postpartum">
    <header className="dash-nav"><Brand onClick={goHome} /><div><button className="emergency-route" onClick={() => openChat("I need urgent help")}><ShieldCheck /> Get urgent help</button>{home.name ? <button className="profile" onClick={() => document.getElementById("explore")?.scrollIntoView({ behavior: "smooth" })} aria-label="Open your sample context"><i>{home.name[0]}</i><b>{home.name}</b></button> : null}<button className="mobile-menu" onClick={() => document.getElementById("explore")?.scrollIntoView({ behavior: "smooth" })} aria-label="Open dashboard sections"><Menu /></button></div></header>
    <section className="welcome"><div><span>YOUR POSTPARTUM SPACE</span><h1>Your space with Maya.</h1><p>Recovery, nourishment, feeding and wellbeing in one calm view.</p></div><button onClick={editDetails}>Edit my details <MoveUpRight /></button></section>
    <DashboardMetrics home={home} editDetails={editDetails} />
    <section className="postpartum-overview">
      <JourneyProgress home={home} />
      <article className="baby-rhythm"><header><span>BABY’S RHYTHM</span><i><Baby /></i></header><h2>Patterns can be added<br /><em>when you choose.</em></h2><div><span><SunMedium /><b>Feeding</b><small>Not provided</small></span><span><MoonStar /><b>Sleep</b><small>Not provided</small></span></div></article>
    </section>
    <ContentTabs home={home} openChat={openChat} runPlan={runPlan} postpartum />
    <button className="floating-chat" onClick={() => openChat()}><i><Flower2 /></i><span><b>Ask Maya</b><small>Here with you</small></span></button>
  </main>;
}

export function WeekLibrary({
  selectedWeek,
  back,
}: {
  selectedWeek: number | null;
  back: () => void;
  home: HomeData;
}) {
  const [activeWeek, setActiveWeek] = useState(selectedWeek || 22);
  const active = getBabyGrowth(activeWeek);
  const hasComparison = activeWeek > 2 && Boolean(active.comparison);
  const activeMeasurements = getGrowthMeasurements(activeWeek);
  const weeks = useMemo(() => Array.from({ length: 41 }, (_, index) => getBabyGrowth(index + 1)), []);

  return <main className="week-library">
    <header><button onClick={back}><ArrowLeft /> Back to dashboard</button><Brand onClick={back} /><span>YOUR WEEK-BY-WEEK SIZE GUIDE</span></header>
    <section className="library-hero"><div><span>WEEK BY WEEK</span><h1>One little story,<br /><em>growing with you.</em></h1><p>A little perspective on every week, with playful size comparisons and fixed reference estimates. Exploring here does not change your onboarding timeline.</p></div><article><div className={`library-pair ${growthStyles.libraryPair}`}>{active.babyAsset ? <BalancedGrowthImage asset={active.babyAsset} label={`Baby illustration, week ${activeWeek}`} /> : null}{active.comparisonAsset ? <BalancedGrowthImage asset={active.comparisonAsset} label={active.comparison} /> : null}</div><span>WEEK {activeWeek}</span><h2>{hasComparison ? <>Your baby is about the size of {/^[aeiou]/i.test(active.comparison) ? "an" : "a"} <em>{active.comparison.toLowerCase()}.</em></> : "Every little beginning has its own story."}</h2><div className="library-measures"><p><small>APPROX. LENGTH</small><b>{activeMeasurements?.length || "Too early"}</b></p><p><small>APPROX. WEIGHT</small><b>{activeMeasurements?.weight || "Too early"}</b></p></div><footer><Info /> A playful comparison, not to scale. These estimates are not measurements of your baby.</footer><details className={growthStyles.details}><summary>About these estimates</summary><p>{activeMeasurements?.length ? `Length: ${activeMeasurements.lengthBasis}.` : activeMeasurements?.earlyNote} {activeMeasurements?.lengthSource ? <a href={activeMeasurements.lengthSource.url} target="_blank" rel="noopener noreferrer">Length source</a> : null}</p><p>{activeMeasurements?.weightSource ? <a href={activeMeasurements.weightSource.url} target="_blank" rel="noopener noreferrer">Weight source · {activeMeasurements.weightBasis}</a> : activeMeasurements?.earlyNote}</p><p>Reference methods vary across weeks; this is not a continuous clinical growth chart.</p></details></article></section>
    <section className="library-grid-section"><header><div><span>THE COMPLETE LIBRARY</span><h2>Weeks 1–41</h2></div><p>A new little perspective, one week at a time.</p></header><div className="library-grid">{weeks.map(item => {
      const available = item.week > 2;
      const measurements = getGrowthMeasurements(item.week);
      return <button key={item.week} className={activeWeek === item.week ? "active" : ""} onClick={() => { setActiveWeek(item.week); window.scrollTo({ top: 0, behavior: "smooth" }); }} aria-label={`Explore week ${item.week}`}><div className={growthStyles.libraryPair}>{item.babyAsset ? <BalancedGrowthImage asset={item.babyAsset} label={`Baby illustration, week ${item.week}`} /> : null}{item.comparisonAsset ? <BalancedGrowthImage asset={item.comparisonAsset} label={item.comparison} /> : null}</div><span>WEEK {item.week}</span><h3>{available ? item.comparison : "Earliest beginning"}</h3><p>{measurements?.length || "Early beginning"}<i />{measurements?.weight || "Weight: too early"}</p></button>;
    })}</div></section>
    <p className="library-note"><Info /> Approximate educational references—not a growth assessment. Your clinician’s scan is your baby’s personal reference.</p>
  </main>;
}

function Intro({ n, title, text }: { n: string; title: string; text: string }) {
  return <div className="plan-intro"><span>{n} / EXPLORE</span><h2>{title}</h2><p>{text}</p></div>;
}
