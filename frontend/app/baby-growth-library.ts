export const comparisonCatalogueApproval = {
  approvalId: "KAJAL-STAGE-1-PRODUCT-REVIEW-2026-09-11",
  reviewer: "Kajal",
  capacity: "Product/content review",
  decisionDate: "2026-09-11",
  catalogueVersion: "1.0.0",
  catalogueSha256: "D3554DFE325FE3DEBF8A7FFF78A391BA262200F885B305C08946448697E247E8",
  decision: "Rounded and repeatable later-week comparison sequence accepted as product direction",
} as const;

export type BabyGrowthWeek = {
  week: number;
  comparison: string;
  comparisonAsset: string | null;
  babyAsset: string | null;
  visualScale: number;
  comparisonReviewState: "product_approved_2026-09-11" | "pending";
  comparisonApprovalId: string | null;
  measurementLength: string | null;
  measurementWeight: string | null;
  measurementSourceId: null;
  measurementReviewState: "pending";
  imageOwnershipOrLicence: "pending";
};

const productApprovedWeeks = new Set([20, 21, 22, 23, 24, 25, 26, 28, 29, 31, 32, 33, 36]);

const row = (
  week: number,
  comparison: string,
  measurementLength: string | null,
  measurementWeight: string | null,
  comparisonAsset: string | null,
  babyAsset: string | null,
  visualScale: number,
): BabyGrowthWeek => ({
  week,
  comparison,
  comparisonAsset,
  babyAsset,
  visualScale,
  comparisonReviewState: productApprovedWeeks.has(week) ? "product_approved_2026-09-11" : "pending",
  comparisonApprovalId: productApprovedWeeks.has(week) ? comparisonCatalogueApproval.approvalId : null,
  measurementLength,
  measurementWeight,
  measurementSourceId: null,
  measurementReviewState: "pending",
  imageOwnershipOrLicence: "pending",
});

export const babyGrowthLibrary: BabyGrowthWeek[] = [
  row(1, "No embryo-size comparison yet", null, null, null, null, .34),
  row(2, "No embryo-size comparison yet", null, null, null, null, .35),
  row(3, "Speck of fine sand", "Microscopic", null, null, "/babies/week-05.png", .36),
  row(4, "Poppy seed", "~1 mm", "<1 g", "/comparisons/poppy-seed.png", "/babies/week-05.png", .38),
  row(5, "Sesame seed", "~2 mm", "<1 g", "/comparisons/sesame-seed.png", "/babies/week-05.png", .40),
  row(6, "Lentil", "~6 mm", "<1 g", "/comparisons/lentil.png", "/babies/week-05.png", .42),
  row(7, "Blueberry", "~10 mm", "<1 g", "/comparisons/blueberry.png", "/babies/week-08.png", .44),
  row(8, "Pumpkin seed", "~16 mm", "~1 g", "/comparisons/pumpkin-seed.png", "/babies/week-08.png", .46),
  row(9, "Rajma bean", "~22 mm", "~2 g", "/comparisons/rajma-bean.png", "/babies/week-08.png", .48),
  row(10, "Cherry", "~30 mm", "~4 g", "/comparisons/cherry.png", "/babies/week-12.png", .50),
  row(11, "Strawberry", "~41 mm", "~7 g", "/comparisons/strawberry.png", "/babies/week-12.png", .52),
  row(12, "Small lime", "~5.4 cm", "~14 g", "/comparisons/lime.png", "/babies/week-12.png", .54),
  row(13, "Lemon", "~7.4 cm", "~23 g", "/comparisons/lemon.png", "/babies/week-12.png", .56),
  row(14, "Guava", "~8.7 cm", "~90 g", "/comparisons/guava.png", "/babies/week-16.png", .58),
  row(15, "Sweet lime (mosambi)", "~10.1 cm", "~114 g", "/comparisons/lime.png", "/babies/week-16.png", .60),
  row(16, "Avocado", "~11.6 cm", "~144 g", "/comparisons/avocado.png", "/babies/week-16.png", .62),
  row(17, "Pomegranate", "~13 cm", "~179 g", "/comparisons/pomegranate.png", "/babies/week-16.png", .64),
  row(18, "Bell pepper (shimla mirch)", "~14.2 cm", "~222 g", "/comparisons/bell-pepper.png", "/babies/week-16.png", .66),
  row(19, "Mango", "~15.3 cm", "~272 g", "/comparisons/mango.png", "/baby-week-22.png", .68),
  row(20, "Small orange", "~25.6 cm", "~330 g", "/comparisons/orange.png", "/baby-week-22.png", .70),
  row(21, "Orange", "~26.7 cm", "~398 g", "/comparisons/orange.png", "/baby-week-22.png", .72),
  row(22, "Grapefruit", "~27.8 cm", "~525 g", "/comparisons/grapefruit.png", "/baby-week-22.png", .74),
  row(23, "Grapefruit", "~28.9 cm", "~592 g", "/comparisons/grapefruit.png", "/baby-week-22.png", .76),
  row(24, "Small muskmelon (kharbuja)", "~30 cm", "~668 g", "/comparisons/muskmelon.png", "/baby-week-22.png", .78),
  row(25, "Small muskmelon (kharbuja)", "~34.6 cm", "~756 g", "/comparisons/muskmelon.png", "/babies/week-26-reference.png", .80),
  row(26, "Small cabbage", "~35.6 cm", "~856 g", "/comparisons/cabbage.png", "/babies/week-26-reference.png", .82),
  row(27, "Cauliflower", "~36.6 cm", "~969 g", "/comparisons/cauliflower.png", "/babies/week-26-reference.png", .84),
  row(28, "Cabbage", "~37.6 cm", "~1,097 g", "/comparisons/cabbage.png", "/babies/week-26-reference.png", .86),
  row(29, "Cabbage", "~38.6 cm", "~1,239 g", "/comparisons/cabbage.png", "/babies/week-26-reference.png", .88),
  row(30, "Cabbage", "~39.9 cm", "~1,396 g", "/comparisons/cabbage.png", "/babies/week-26-reference.png", .90),
  row(31, "Honeydew melon", "~41.1 cm", "~1,568 g", "/comparisons/honeydew-melon.png", "/babies/week-26-reference.png", .92),
  row(32, "Honeydew melon", "~42.4 cm", "~1,755 g", "/comparisons/honeydew-melon.png", "/babies/week-26-reference.png", .94),
  row(33, "Small watermelon", "~43.7 cm", "~1,954 g", "/comparisons/watermelon.png", "/baby-week-22.png", .95),
  row(34, "Muskmelon (kharbuja)", "~45 cm", "~2,162 g", "/comparisons/muskmelon.png", "/baby-week-22.png", .96),
  row(35, "Large honeydew melon", "~46.2 cm", "~2,378 g", "/comparisons/honeydew-melon.png", "/baby-week-22.png", .97),
  row(36, "Large muskmelon", "~47.4 cm", "~2,594 g", "/comparisons/muskmelon.png", "/baby-week-22.png", .98),
  row(37, "Small pumpkin", "~48.6 cm", "~2,806 g", "/comparisons/pumpkin.png", "/baby-week-22.png", .99),
  row(38, "Medium pumpkin", "~49.8 cm", "~3,006 g", "/comparisons/pumpkin.png", "/baby-week-22.png", 1),
  row(39, "Small watermelon", "~50.7 cm", "~3,186 g", "/comparisons/watermelon.png", "/baby-week-22.png", 1.01),
  row(40, "Full-size watermelon", "~51.2 cm", "~3,338 g", "/comparisons/watermelon.png", "/baby-week-22.png", 1.02),
  row(41, "Large watermelon", "~51.7 cm", "~3,500 g", "/comparisons/watermelon.png", "/baby-week-22.png", 1.03),
];

export const getBabyGrowth = (week: number) =>
  babyGrowthLibrary[Math.max(1, Math.min(41, week)) - 1];

// Weeks 22-40 in the planning library match the 50th-centile values in the
// INTERGROWTH-21st estimated fetal-weight table. These are population
// references, not a weight measured for this user's baby.
export const getIntergrowthWeightReference = (week: number) => {
  if (week < 22 || week > 40) return null;
  return {
    weight: getBabyGrowth(week).measurementWeight,
    basis: `50th-centile estimated fetal weight at exactly ${week} weeks`,
    sourceTitle: "INTERGROWTH-21st estimated fetal weight table",
    sourceUrl: "https://media.tghn.org/medialibrary/2017/03/GROW_EFW_ct_Table.pdf",
  };
};

// Source-linked general week references, not measurements of an individual baby.
// The broader planning table above has no clinical measurement approval or source IDs.
export const generalWeekMeasurementReferences: Record<number, {
  length: string;
  basis: string;
  sourceTitle: string;
  sourceUrl: string;
}> = {
  5: {
    length: "around 2 mm",
    basis: "embryo length",
    sourceTitle: "NHS week 5 guide",
    sourceUrl: "https://www.nhs.uk/best-start-in-life/pregnancy/week-by-week-guide-to-pregnancy/1st-trimester/week-5/",
  },
  6: {
    length: "around 6 mm",
    basis: "embryo length",
    sourceTitle: "NHS week 6 guide",
    sourceUrl: "https://www.nhs.uk/best-start-in-life/pregnancy/week-by-week-guide-to-pregnancy/1st-trimester/week-6/",
  },
  26: {
    length: "around 35.6 cm",
    basis: "head-to-heel length",
    sourceTitle: "NHS week 26 guide",
    sourceUrl: "https://www.nhs.uk/best-start-in-life/pregnancy/week-by-week-guide-to-pregnancy/2nd-trimester/week-26/",
  },
};
