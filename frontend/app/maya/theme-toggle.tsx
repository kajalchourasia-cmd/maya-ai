"use client";

import { useEffect, useState } from "react";
import { MoonStar, SunMedium } from "lucide-react";

/** Visual experiment only: never reads or persists journey/health information. */
export function ThemeToggle() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    document.documentElement.dataset.mayaTheme = dark ? "purple" : "light";
  }, [dark]);

  return <button
    type="button"
    className="maya-theme-toggle"
    role="switch"
    aria-checked={dark}
    aria-label="Purple dark theme"
    title={dark ? "Switch to the original light theme" : "Try the purple dark theme"}
    onClick={() => setDark(value => !value)}
  >
    {dark ? <MoonStar aria-hidden="true" /> : <SunMedium aria-hidden="true" />}
    <span>{dark ? "Purple dusk" : "Light theme"}</span>
    <i aria-hidden="true"><b /></i>
  </button>;
}
