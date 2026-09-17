"use client";
import { createContext } from "react";
import type { PlanResponse } from "@/lib/maya-api";

// Memory only. Editing onboarding clears the old plan; refresh starts afresh.
export const LatestPlanContext = createContext<PlanResponse | null>(null);
