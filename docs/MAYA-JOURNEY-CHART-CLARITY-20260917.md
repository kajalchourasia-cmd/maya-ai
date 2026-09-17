# Journey chart clarity — 17 September 2026

Scope: chart title, hormone explanations, and a fixed current-timeline badge. No backend, model, corpus, onboarding, or plan changes. No video recorded or paid API calls made.

## Implemented

- User-selected title: “Your body’s changing rhythm”. Description: “Explore the hormone patterns that support pregnancy, week by week.”
- Week/trimester badge matches Growth at a Glance: sentence case, 11px, weight 750, pale blush pill. It derives only from the onboarding timeline, never the exploration slider or pointer.
- Approximate month-derived ranges stay approximate; weeks 41–42 retain their actual badge rather than displaying week 40.
- Hovering a plotted line identifies the nearest hormone using the same interpolation that draws the curve.
- Legend buttons also reveal explanations on keyboard focus or tap.
- Pointer tooltip appears 14px below the pointer and follows its position, with horizontal edge clamping. Keyboard focus retains a stable fallback position. Native SVG title tooltips were removed to avoid duplicate labels.
- Plain-language roles: hCG (supports early pregnancy), progesterone (helps maintain pregnancy), estrogen (supports pregnancy-related growth).
- Existing educational limitation and source remain. These are illustrative relative patterns, not measurements or mood forecasts.

Source: [Endotext: Endocrinology of Pregnancy](https://www.ncbi.nlm.nih.gov/books/NBK278962/).

## Verification

- TypeScript `tsc --noEmit`: passed.
- Frontend test suite after the final wording/tooltip update: 41 passed, 0 failed.
- Browser checked final title, description, matching badge appearance, and tooltip movement at two positions along the hCG curve. Current-week badge remained unchanged.
- Browser at port 5180: visually checked layout; hCG line hover displayed its explanation; progesterone and estrogen legend buttons displayed their explanations.
- Moved exploration slider from week 22 to 30: actual week-22/second-trimester badge stayed unchanged. Restored slider to week 22 afterward.
- Tests cover trimester boundaries, weeks 41–42, approximate month ranges, postpartum preservation, all three curve hit targets, and blank chart space.

Voice selection is a separate future step. Playwright records the browser; narration comes from a separate voice engine. Select short voice samples before recording the complete video.
