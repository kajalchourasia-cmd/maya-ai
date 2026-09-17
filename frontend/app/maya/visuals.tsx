"use client";
/* eslint-disable @next/next/no-img-element */

import type { CSSProperties, ReactNode } from "react";
import { Flower2, RotateCcw, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getBabyGrowth } from "../baby-growth-library";
import { growthAssetBounds } from "../growth-asset-bounds";

export function BalancedGrowthImage({ asset, label }: { asset: string; label: string }) {
  const dimensions = growthAssetBounds[asset];
  if (!dimensions) return <img src={asset} alt={label} />;
  const [x, y, right, bottom] = dimensions.bounds;
  return <svg role="img" aria-label={label} viewBox={`${x} ${y} ${right - x} ${bottom - y}`} preserveAspectRatio="xMidYMid meet">
    <image href={asset} width={dimensions.size[0]} height={dimensions.size[1]} />
  </svg>;
}

export function Brand({ light = false, onClick }: { light?: boolean; onClick?: () => void }) {
  return <button type="button" className={`brand ${light ? "light" : ""}`} onClick={onClick} aria-label="Maya home"><i><Flower2 /></i><b>maya</b></button>;
}

export function FetalVisual({ week, compact = false }: { week: number; compact?: boolean }) {
  const data = getBabyGrowth(week);
  const displayScale = compact ? data.visualScale : Math.min(1.18, data.visualScale * 2.1);
  return <span
    className={`fetal-visual ${compact ? "compact" : ""}`}
    aria-label={week <= 2 ? `Pregnancy week ${week}; no embryo illustration is shown` : `Baby illustration for pregnancy week ${week}`}
    style={{ "--growth-scale": displayScale } as CSSProperties}
  >
    {data.babyAsset ? <img src={data.babyAsset} alt="" /> : <span className="pre-stage"><i /><i /><i /></span>}
  </span>;
}

export function FruitVisual({ week, compact = false }: { week: number; compact?: boolean }) {
  const data = getBabyGrowth(week);
  const displayScale = compact ? data.visualScale : Math.min(1.18, data.visualScale * 2.1);
  return <span
    className={`fruit-visual ${compact ? "compact" : ""} ${data.comparisonAsset ? "" : "waiting"}`}
    aria-label={data.comparison}
    style={{ "--growth-scale": displayScale } as CSSProperties}
  >
    {data.comparisonAsset ? <img src={data.comparisonAsset} alt={`Size comparison: ${data.comparison}`} /> : <i />}
  </span>;
}

export function ProductPreviewBadge() {
  return <span className="product-preview-badge"><ShieldCheck /> Capstone Product Preview</span>;
}

export function PreviewFooter() {
  return <p className="preview-footer"><ShieldCheck /> Educational support—not diagnosis or emergency care.</p>;
}

export function StatusPanel({
  title,
  message,
  tone = "unavailable",
  action,
  actionLabel,
}: {
  title: string;
  message: string;
  tone?: "unavailable" | "error" | "empty" | "safety";
  action?: () => void;
  actionLabel?: string;
}) {
  return <div className={`status-panel ${tone}`} role={tone === "error" || tone === "safety" ? "alert" : "status"}>
    <ShieldCheck />
    <div><b>{title}</b><p>{message}</p>{action && actionLabel ? <Button onClick={action}><RotateCcw /> {actionLabel}</Button> : null}</div>
  </div>;
}

export function SectionShell({ children }: { children: ReactNode }) {
  return <section className="section-shell">{children}</section>;
}
