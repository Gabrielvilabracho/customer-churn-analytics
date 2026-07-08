import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import DashboardPage from "./page";

const dashboardPayload = {
  artifact_version: "run-2026-07-02",
  freshness: { metrics_created_at_utc: "2026-07-02T00:00:00Z" },
  kpis: { pr_auc: 0.82, recall: 0.74, precision: 0.61 },
  risk_distribution: { high: 1, low: 1 },
  prediction_samples: [
    sample("sample-001", "Sample 001", "0.81", "Month-to-month", "3", "Electronic check", "91.25", "Fiber optic"),
    sample("sample-002", "Sample 002", "0.16", "Two year", "52", "Credit card", "42", "DSL"),
  ],
};

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("DashboardPage", () => {
  it("renders API-backed KPI cards, cohorts, and risk rows", async () => {
    vi.stubEnv("CHURN_API_BASE_URL", "http://localhost:8000");
    vi.stubGlobal("fetch", async () => Response.json(dashboardPayload));

    const html = renderToStaticMarkup(await DashboardPage({}));

    expect(html).toContain("Executive churn command center");
    expect(html).toContain("Model PR-AUC");
    expect(html).toContain("0.82");
    expect(html).toContain("Month-to-month");
    expect(html).toContain("High risk");
    expect(html).toContain("run-2026-07-02");
  });

  it("renders an actionable degraded state instead of invented analytics", async () => {
    vi.stubEnv("CHURN_API_BASE_URL", "http://localhost:8000");
    vi.stubGlobal("fetch", async () => Response.json({ status: "degraded", reason: "metrics artifact is missing" }, { status: 503 }));

    const html = renderToStaticMarkup(await DashboardPage({}));

    expect(html).toContain("Analytics artifacts are unavailable");
    expect(html).toContain("metrics artifact is missing");
    expect(html).toContain("Run the ML training pipeline and refresh the API artifacts.");
  });
});

function sample(sample_id: string, display_reference: string, churn_probability: string, Contract: string, tenure: string, PaymentMethod: string, MonthlyCharges: string, InternetService: string) {
  return { sample_id, display_reference, churn_probability, Contract, tenure, PaymentMethod, MonthlyCharges, InternetService };
}
