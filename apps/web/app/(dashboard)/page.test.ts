import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import DashboardPage from "./page";

const dashboardPayload = {
  artifact_version: "run-2026-07-02",
  freshness: { metrics_created_at_utc: "2026-07-02T00:00:00Z" },
  kpis: { pr_auc: 0.82, recall: 0.74, precision: 0.61 },
  risk_distribution: { high: 1, low: 1 },
  prediction_samples: [
    sample("student-001", "Student 001", "0.81", "Engineering", "15", "High", "Restrictive"),
    sample("student-002", "Student 002", "0.16", "Business", "2", "Low", "Permissive"),
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

    expect(html).toContain("Student burnout-risk command center");
    expect(html).toContain("Student retention intelligence");
    expect(html).toContain("Model PR-AUC");
    expect(html).toContain("0.82");
    expect(html).toContain("Engineering");
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

function sample(sample_id: string, display_reference: string, churn_probability: string, Major_Category: string, Weekly_GenAI_Hours: string, Perceived_AI_Dependency: string, Institutional_Policy: string) {
  return { sample_id, display_reference, churn_probability, Major_Category, Weekly_GenAI_Hours, Perceived_AI_Dependency, Institutional_Policy };
}
