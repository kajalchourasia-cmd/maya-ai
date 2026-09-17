"use client";

import { useEffect, useState } from "react";
import type {
  HomeData, JourneyKind, MayaDisplay, OnboardingPayload, OnboardingResult, PlanResponse,
} from "@/lib/maya-api";
import { MayaApiError, mayaApi } from "@/lib/maya-api";
import { Chat } from "./maya/chat";
import type { ChatMessage } from "./maya/chat";
import { PregnancyDashboard, PostpartumDashboard, WeekLibrary } from "./maya/dashboard";
import { Landing, Onboarding } from "./maya/onboarding";
import { LatestPlanContext } from "./maya/plan-context";

type View = "landing" | "onboarding" | "dashboard" | "chat" | "library";
type Focus = "balanced" | "nutrition" | "movement" | "wellbeing";

export default function Home() {
  const [view, setView] = useState<View>("landing");
  const [sessionId, setSessionId] = useState("");
  const [lastPayload, setLastPayload] = useState<OnboardingPayload | null>(null);
  const [homeData, setHomeData] = useState<HomeData | null>(null);
  const [journey, setJourney] = useState<JourneyKind>("pregnant");
  const [appError, setAppError] = useState("");
  const [onboardingNotice, setOnboardingNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [chatQuestion, setChatQuestion] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [latestPlan, setLatestPlan] = useState<PlanResponse | null>(null);

  const rememberSession = (id: string) => {
    setSessionId(id);
  };

  const clearSessionIdentity = () => {
    setSessionId("");
  };

  const clearSession = () => {
    setLatestPlan(null);
    clearSessionIdentity();
    setHomeData(null);
    setChatMessages([]);
    setChatQuestion("");
  };

  const rememberPayload = (payload: OnboardingPayload) => {
    const cached = { ...payload, session_id: undefined };
    setLastPayload(cached);
  };

  const clearPayload = () => {
    setLastPayload(null);
  };

  const createSession = async () => {
    const session = await mayaApi.createSession();
    rememberSession(session.session_id);
    return session.session_id;
  };

  const begin = () => {
    clearSession();
    clearPayload();
    setAppError("");
    setOnboardingNotice("");
    setView("onboarding");
    setBusy(true);
    void createSession().catch(reason => {
      setOnboardingNotice(reason instanceof Error ? reason.message : "The Maya API is unavailable.");
    }).finally(() => setBusy(false));
  };

  const finishOnboarding = async (payload: OnboardingPayload): Promise<OnboardingResult> => {
    setLatestPlan(null);
    setOnboardingNotice("");
    let sid = payload.session_id || sessionId;
    if (!sid) sid = await createSession();
    const submitted = { ...payload, session_id: sid };
    let resolved: OnboardingResult;
    try {
      resolved = await mayaApi.onboard(submitted);
    } catch (reason) {
      if (!(reason instanceof MayaApiError) || !reason.isMissingSession) throw reason;
      clearSession();
      sid = await createSession();
      resolved = await mayaApi.onboard({ ...payload, session_id: sid });
    }
    rememberPayload(payload);
    rememberSession(resolved.session_id);
    setChatMessages([{ from: "maya", text: `Hi${payload.name ? ` ${payload.name}` : ""}. What’s on your mind today?` }]);
    setChatQuestion("");
    setJourney(payload.journey);
    if (resolved.safety_blocked) return resolved;
    const nextHome = await mayaApi.home(resolved.session_id);
    setHomeData(nextHome);
    setView("dashboard");
    return resolved;
  };

  const withRecoveredSession = async <T,>(operation: (id: string) => Promise<T>): Promise<T> => {
    if (!sessionId) {
      setOnboardingNotice("Add your journey before using this feature.");
      setView("onboarding");
      throw new Error("Add your journey before using this feature.");
    }
    try {
      return await operation(sessionId);
    } catch (reason) {
      if (!(reason instanceof MayaApiError) || !reason.isMissingSession) throw reason;
      clearSessionIdentity();
      if (!lastPayload) {
        setOnboardingNotice("The local server restarted. Please add your journey again.");
        setView("onboarding");
        throw new Error("The local preview restarted. Please complete onboarding again.");
      }
      const recoveredId = await createSession();
      const recovered = await mayaApi.onboard({ ...lastPayload, session_id: recoveredId });
      if (recovered.safety_blocked) {
        setOnboardingNotice("The recovered session needs urgent safety review before continuing.");
        setView("onboarding");
        throw new Error("Urgent safety review is required before continuing.");
      }
      const nextHome = await mayaApi.home(recoveredId);
      setHomeData(nextHome);
      setJourney(lastPayload.journey);
      return operation(recoveredId);
    }
  };

  const runPlan = async (focus: Focus) => {
    const result = await withRecoveredSession(id => mayaApi.plan(id, focus));
    setLatestPlan(result);
    return result;
  };
  const runChat = (text: string): Promise<MayaDisplay> =>
    withRecoveredSession(id => mayaApi.chat(id, text).then(response => {
      if (response.schedule) setLatestPlan({ ...response, schedule: response.schedule, save_available: false, fictional: false });
      return { ...response.display, schedule: response.schedule };
    }));

  const openChat = (question = "") => {
    setChatQuestion(question);
    setView("chat");
  };

  const openLandingChat = () => {
    begin();
    setOnboardingNotice("Add your journey first so Ask Maya knows which week or postpartum position you selected.");
  };

  const editDetails = () => {
    setOnboardingNotice("");
    setView("onboarding");
  };

  useEffect(() => {
    const context = (document as Document & {
      modelContext?: {
        registerTool: (tool: unknown, options?: { signal?: AbortSignal }) => void | Promise<void>;
      };
    }).modelContext;
    if (!context?.registerTool) return;
    const lifecycle = new AbortController();
    Promise.resolve(context.registerTool({
      name: "open_maya_view",
      title: "Open a Maya view",
      description: "Navigate Maya to the landing page, onboarding, dashboard, Ask Maya, or the editorial week library.",
      inputSchema: {
        type: "object",
        properties: { view: { type: "string", enum: ["landing", "onboarding", "dashboard", "chat", "library"] } },
        required: ["view"],
        additionalProperties: false,
      },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute(input: unknown) {
        const next = (input as { view?: string })?.view;
        if (!["landing", "onboarding", "dashboard", "chat", "library"].includes(next || "")) {
          throw new Error("Choose a valid Maya view.");
        }
        if ((next === "dashboard" || next === "library") && !homeData) {
          throw new Error("Complete onboarding before opening that view.");
        }
        setView(next as View);
        return { view: next, status: "opened" };
      },
    }, { signal: lifecycle.signal })).catch(() => {});
    return () => lifecycle.abort();
  }, [homeData]);

  if (view === "onboarding") {
    return <Onboarding back={() => setView(homeData ? "dashboard" : "landing")} done={finishOnboarding} initialError={onboardingNotice} initialValues={lastPayload} />;
  }
  if (view === "dashboard" && homeData) {
    return <LatestPlanContext.Provider value={latestPlan}>{journey === "postpartum"
      ? <PostpartumDashboard home={homeData} openChat={openChat} goHome={() => setView("landing")} editDetails={editDetails} runPlan={runPlan} />
      : <PregnancyDashboard home={homeData} openChat={openChat} goHome={() => setView("landing")} editDetails={editDetails} openLibrary={() => setView("library")} runPlan={runPlan} />}</LatestPlanContext.Provider>;
  }
  if (view === "library" && homeData && journey === "pregnant") {
    return <WeekLibrary selectedWeek={homeData.journey.exact} back={() => setView("dashboard")} home={homeData} />;
  }
  if (view === "chat" && homeData) {
    return <Chat
      key={chatQuestion || "free-text"}
      name={homeData.name}
      journey={journey}
      journeyLabel={homeData.journey_label}
      back={() => { setChatQuestion(""); setView("dashboard"); }}
      runChat={runChat}
      initialQuestion={chatQuestion}
      messages={chatMessages}
      setMessages={setChatMessages}
    />;
  }
  if (view === "chat" && !homeData) {
    return <Onboarding back={() => setView("landing")} done={finishOnboarding} initialError={onboardingNotice || "Add your journey first so Ask Maya has your week or postpartum position."} />;
  }
  return <Landing start={begin} chat={openLandingChat} busy={busy} error={appError} retry={begin} />;
}
