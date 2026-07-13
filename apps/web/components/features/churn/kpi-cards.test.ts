import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { KpiCards } from "./kpi-cards";
import type { KpiCardModel } from "./dashboard-model";

const kpis: KpiCardModel[] = [
  { label: "Model PR-AUC", value: "0.82", detail: "run-2026-07-02" },
  { label: "Average burnout risk", value: "47%", detail: "3 sampled students" },
];

describe("KpiCards", () => {
  it("uses a student burnout-risk aria-label coherent with the dashboard title", () => {
    const html = renderToStaticMarkup(KpiCards({ cards: kpis }));

    expect(html).toContain('aria-label="Student burnout-risk KPIs"');
  });

  it("renders the label, value, and detail for each KPI card", () => {
    const html = renderToStaticMarkup(KpiCards({ cards: kpis }));

    expect(html).toContain("Model PR-AUC");
    expect(html).toContain("0.82");
    expect(html).toContain("Average burnout risk");
    expect(html).toContain("47%");
  });

  it("preserves the burnout-risk aria-label even when no cards are provided", () => {
    const html = renderToStaticMarkup(KpiCards({ cards: [] }));

    expect(html).toContain('aria-label="Student burnout-risk KPIs"');
    // No card content rendered
    expect(html).not.toContain("Model PR-AUC");
  });
});
