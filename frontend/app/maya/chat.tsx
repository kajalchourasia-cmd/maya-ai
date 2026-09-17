"use client";

import { useEffect, useRef, useState } from "react";
import type { Dispatch, SetStateAction } from "react";
import { ArrowLeft, ArrowRight, FileText, Flower2, Send, ShieldCheck, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { EvidenceCitation, JourneyKind, MayaDisplay } from "@/lib/maya-api";
import { Brand, PreviewFooter, StatusPanel } from "./visuals";
import { WeeklySchedule } from "./weekly-schedule";

const provenanceLabels = [
  "Your confirmed information",
  "Your uploaded record says",
  "You reported",
  "Public guidance says",
  "Needs confirmation",
];

export type ChatMessage = { from: "maya" | "you"; text: string; display?: MayaDisplay; errorCode?: string };

export function Chat({
  name,
  journey,
  journeyLabel,
  back,
  runChat,
  initialQuestion,
  messages,
  setMessages,
}: {
  name: string;
  journey: JourneyKind;
  journeyLabel: string;
  back: () => void;
  runChat: (text: string) => Promise<MayaDisplay>;
  initialQuestion?: string;
  messages: ChatMessage[];
  setMessages: Dispatch<SetStateAction<ChatMessage[]>>;
}) {
  const suggestions = journey === "postpartum"
    ? ["Show easy nourishment options", "Create a wellbeing support plan", "Questions for my next appointment"]
    : ["Show meal options", "Create a weekly movement plan", "Questions for my next appointment"];
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [lastFailed, setLastFailed] = useState("");
  const [drawer, setDrawer] = useState<EvidenceCitation | null>(null);
  const initialSent = useRef(false);
  const active = useRef(true);
  const conversationEnd = useRef<HTMLDivElement>(null);
  useEffect(() => {
    conversationEnd.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, sending]);
  useEffect(() => {
    active.current = true;
    return () => { active.current = false; };
  }, []);

  const send = async (text: string) => {
    if (!text.trim() || sending) return;
    const question = text.trim();
    setMessages(current => [...current, { from: "you", text: question }]);
    setInput("");
    setLastFailed("");
    setSending(true);
    try {
      const display = await runChat(question);
      if (!active.current) return;
      setMessages(current => [...current, { from: "maya", text: display.summary, display }]);
    } catch (reason) {
      if (!active.current) return;
      const message = reason instanceof Error ? reason.message : "Maya could not answer right now.";
      const code = reason && typeof reason === "object" && "code" in reason ? String(reason.code) : "request_failed";
      setMessages(current => [...current, { from: "maya", text: message, errorCode: code }]);
      if (code !== "corpus_not_connected") setLastFailed(question);
    } finally {
      setSending(false);
    }
  };

  useEffect(() => {
    if (initialQuestion && !initialSent.current) {
      initialSent.current = true;
      void send(initialQuestion);
    }
  // The first displayed suggestion is intentionally submitted once on entry.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuestion]);

  return <main className="chat">
    <header><button onClick={back} aria-label="Back to dashboard"><ArrowLeft /></button><Brand onClick={back} /><button onClick={back} aria-label="Close conversation"><X /></button></header>
    <section>
      <div className="chat-context"><span>{journeyLabel.toUpperCase()}</span><p>Maya uses the timeline and preferences you entered during onboarding. Safety runs before ordinary response generation.</p></div>
      <div className="messages" aria-live="polite">
        {messages.map((message, index) => <article className={`${message.from} ${message.display?.route === "urgent" ? "urgent-message" : ""}`} key={`${index}-${message.text.slice(0, 20)}`}>
          <i>{message.from === "maya" ? <Flower2 /> : (name[0] || "Y")}</i>
          <div>
            <p>{message.display ? <b>{message.display.title}<br /></b> : null}{message.text}</p>
            {message.display?.schedule ? <WeeklySchedule schedule={message.display.schedule} /> : null}
            {message.display?.provenance_sections ? <div className="provenance-groups">{provenanceLabels.map(label => {
              const values = message.display?.provenance_sections[label] || [];
              return values.length ? <section key={label}><b>{label}</b>{values.map(value => <p key={value}>{value}</p>)}</section> : null;
            })}</div> : null}
            {message.display?.applied_constraints.length ? <small>Based on your information: {message.display.applied_constraints.join(", ")}</small> : null}
            {message.display?.uncertainties.length ? <div className="chat-uncertainty"><b>Important context</b><p>{message.display.uncertainties.join(" ")}</p></div> : null}
            {message.display?.citations.length ? <div className="citation-row">{message.display.citations.map(citation => <button onClick={() => setDrawer(citation)} key={`${citation.evidence_id}-${citation.locator}`}><FileText /> {citation.evidence_id}</button>)}</div> : null}
            {message.display?.route === "urgent" ? <small><ShieldCheck /> Ordinary generation calls: {message.display.ordinary_generation_calls}</small> : null}
          </div>
        </article>)}
        {messages.length === 1 ? <div className="suggestions">{suggestions.map(question => <button onClick={() => void send(question)} key={question}>{question}<ArrowRight /></button>)}</div> : null}
        {sending ? <article className="maya loading-chat"><i><Flower2 /></i><div className="typing-dots" role="status" aria-label="Maya is preparing your answer"><span /><span /><span /></div></article> : null}
        {lastFailed ? <StatusPanel tone="error" title="Answer not completed" message="Maya could not complete this answer. You can retry when the service is available." action={() => void send(lastFailed)} actionLabel="Retry question" /> : null}
        <div ref={conversationEnd} />
      </div>
    </section>
    <footer><div><Input value={input} disabled={sending} onChange={event => setInput(event.target.value)} onKeyDown={event => { if (event.key === "Enter") void send(input); }} placeholder="Ask what’s on your mind…" /><Button disabled={sending || !input.trim()} onClick={() => void send(input)} aria-label="Send message"><Send /></Button></div><PreviewFooter /></footer>
    {drawer ? <aside className="evidence-drawer" aria-label="Evidence details">
      <header><div><span>{drawer.source_type === "catalogue_education" ? "SOURCE-LINKED EDUCATION" : drawer.source_type === "development_source" ? "SOURCE EVIDENCE · DEVELOPMENT" : drawer.source_type === "public_fixture" ? "PUBLIC GUIDANCE" : "SAMPLE RECORD"}</span><h2>{drawer.source_title}</h2></div><button onClick={() => setDrawer(null)} aria-label="Close evidence details"><X /></button></header>
      <dl><div><dt>Publisher</dt><dd>{drawer.publisher}</dd></div><div><dt>Evidence ID</dt><dd>{drawer.evidence_id}</dd></div><div><dt>Locator</dt><dd>{drawer.locator}</dd></div><div><dt>Review status</dt><dd>{drawer.review_status}</dd></div><div><dt>Supports this claim</dt><dd>{drawer.supports_claim ? "Yes" : "No—shown as insufficient evidence"}</dd></div></dl>
      <blockquote>{drawer.supporting_passage}</blockquote>
      {drawer.url && /^https:\/\//.test(drawer.url) ? <a href={drawer.url} target="_blank" rel="noreferrer">Read the original source</a> : null}
      <p><ShieldCheck /> {drawer.source_type === "catalogue_education" ? "Authored educational summary, not a quotation or a measurement of your baby. See the original source for context." : drawer.source_type === "development_source" ? "Original source passage. Automated support checks are not clinical review or publication approval." : "Product Preview evidence. Source eligibility and exact span were checked before display."}</p>
    </aside> : null}
  </main>;
}
