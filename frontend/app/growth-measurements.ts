// Fixed educational lookup; no model calls, interpolation or personal scan data.
// Checked 2026-09-16. Length and weight may use different reference populations.
import { getBabyGrowth, getIntergrowthWeightReference } from "./baby-growth-library";

const chart = "https://babyyourbaby.org/pregnancy/during-pregnancy/fetal-chart/";
const nhs = (week: number) => `https://www.nhs.uk/best-start-in-life/pregnancy/week-by-week-guide-to-pregnancy/${week < 13 ? "1st" : "2nd"}-trimester/week-${week}/`;
// Baby Your Baby chart, metric columns, weeks 8–41. Week 20 uses the
// head-to-heel NHS reference instead of mixing it with the chart's CRL value.
const lengths = [1.6, 2.3, 3.1, 4.1, 5.4, 7.4, 8.7, 10.1, 11.6, 13, 14.2, 15.3, 25.6, 26.7, 27.8, 28.9, 30, 34.6, 35.6, 36.6, 37.6, 38.6, 39.9, 41.1, 42.4, 43.7, 45, 46.2, 47.4, 48.6, 49.8, 50.7, 51.2, 51.7];
const earlyWeights = [1, 2, 4, 7, 14, 23, 43, 70, 100, 140, 190, 240, 300, 360];

export function getGrowthMeasurements(week: number) {
  if (!Number.isInteger(week) || week < 1 || week > 41) return null;
  const earlyLength = ({ 4: 2, 5: 2, 6: 6, 7: 10 } as Record<number, number>)[week];
  const length = week >= 8 ? `~${lengths[week - 8]} cm` : earlyLength ? `~${earlyLength} mm` : null;
  const intergrowth = getIntergrowthWeightReference(week);
  const weight = intergrowth?.weight ?? (week >= 8 && week <= 21 ? `~${earlyWeights[week - 8]} g` : week === 41 ? "~3,597 g" : null);
  return {
    week, length, weight,
    lengthBasis: week < 20 ? "Head to bottom (crown–rump)" : "Head to heel",
    lengthSource: length ? { title: week <= 7 || week === 20 ? `NHS week ${week}` : "Baby Your Baby · fetal growth chart", url: week <= 7 || week === 20 ? nhs(week) : chart } : null,
    weightSource: weight ? { title: intergrowth ? intergrowth.sourceTitle : "Baby Your Baby · fetal growth chart", url: intergrowth ? intergrowth.sourceUrl : chart } : null,
    weightBasis: intergrowth ? "50th-centile estimated fetal weight" : "General week reference",
    earlyNote: week <= 2 ? "Pregnancy dating starts before there is an embryo to measure." : week <= 3 ? "An early beginning—too small for a useful size estimate." : "Weight is not estimated in this early-week reference.",
    comparison: getBabyGrowth(week).comparison,
  };
}
