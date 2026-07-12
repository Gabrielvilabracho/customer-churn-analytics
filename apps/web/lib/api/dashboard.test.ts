import { afterEach, describe, expect, it, vi } from "vitest";

import { DashboardAnalyticsError, fetchDashboardAnalytics } from "./client";
import type { PredictionSample } from "./types";

const dashboardPayload = {
  artifact_version: "run-2026-07-07",
  freshness: { metrics_created_at_utc: "2026-07-07T00:00:00Z" },
  kpis: { pr_auc: 0.79, recall: 0.71 },
  risk_distribution: { high: 150, low: 450 },
  threshold: 0.65,
  prediction_samples: [
    {
      sample_id: "student-001",
      display_reference: "Student 001",
      churn_probability: "0.88",
      Major_Category: "Engineering",
      Weekly_GenAI_Hours: "15",
      Perceived_AI_Dependency: "High",
      Institutional_Policy: "Restrictive",
    },
    {
      sample_id: "student-002",
      display_reference: "Student 002",
      churn_probability: "0.42",
      Major_Category: "Arts",
      Weekly_GenAI_Hours: "4",
      Perceived_AI_Dependency: "Low",
      Institutional_Policy: "Permissive",
    },
  ],
};

const educationPayload = {
  artifact_version: "run-2026-07-07",
  freshness: { metrics_created_at_utc: "2026-07-07T00:00:00Z" },
  kpis: { pr_auc: 0.79, recall: 0.71 },
  risk_distribution: { high: 150, low: 450 },
  threshold: 0.65,
  prediction_samples: [
    {
      sample_id: "student-001",
      display_reference: "Student 001",
      churn_probability: "0.88",
      Major_Category: "Engineering",
      Weekly_GenAI_Hours: "15",
      Perceived_AI_Dependency: "High",
      Institutional_Policy: "Restrictive",
    },
    {
      sample_id: "student-002",
      display_reference: "Student 002",
      churn_probability: "0.42",
      Major_Category: "Arts",
      Weekly_GenAI_Hours: "4",
      Perceived_AI_Dependency: "Low",
      Institutional_Policy: "Permissive",
    },
  ],
};

const telcoOnlyPayload = {
  artifact_version: "run-legacy-telco",
  freshness: {},
  kpis: { pr_auc: 0.5 },
  risk_distribution: { high: 1, low: 1 },
  prediction_samples: [
    {
      sample_id: "telco-001",
      display_reference: "Telco Customer",
      churn_probability: "0.91",
      Contract: "Month-to-month",
      tenure: "3",
      PaymentMethod: "Electronic check",
      MonthlyCharges: "91.25",
      InternetService: "Fiber optic",
    },
  ],
};

afterEach(() => {
  vi.useRealTimers();
});

describe("fetchDashboardAnalytics", () => {
  it("loads enriched dashboard analytics from the configured API base URL", async () => {
    const requests: string[] = [];
    const result = await fetchDashboardAnalytics(async (input) => {
      requests.push(String(input));
      return Response.json(dashboardPayload);
    }, "http://localhost:8000");

    expect(requests).toEqual(["http://localhost:8000/analytics/dashboard"]);
    expect(result.artifactVersion).toBe("run-2026-07-07");
    expect(result.threshold).toBe(0.65);
    expect(result.predictionSamples[0]).toMatchObject({
      sampleId: "student-001",
      displayReference: "Student 001",
      majorCategory: "Engineering",
      weeklyGenAiHours: 15,
      perceivedAiDependency: "High",
      institutionalPolicy: "Restrictive",
    });
  });

  it("passes the optional dashboard scenario as a query parameter", async () => {
    const requests: string[] = [];

    await fetchDashboardAnalytics(
      async (input) => {
        requests.push(String(input));
        return Response.json(dashboardPayload);
      },
      "http://localhost:8000",
      { dashboardScenario: "degraded" },
    );

    expect(requests).toEqual(["http://localhost:8000/analytics/dashboard?scenario=degraded"]);
  });

  it("raises an actionable dashboard error when artifacts are degraded", async () => {
    const fetcher = async () => Response.json({ status: "degraded", reason: "metrics artifact is missing" }, { status: 503 });

    await expect(fetchDashboardAnalytics(fetcher, "http://localhost:8000")).rejects.toThrow(DashboardAnalyticsError);
    await expect(fetchDashboardAnalytics(fetcher, "http://localhost:8000")).rejects.toMatchObject({ message: "metrics artifact is missing", status: 503 });
  });

  it("fails fast with a bounded timeout when dashboard analytics do not respond", async () => {
    vi.useFakeTimers();
    const fetcher = (_input: string, init?: RequestInit) =>
      new Promise<Response>((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () => reject(new Error("aborted")));
      });

    const request = fetchDashboardAnalytics(fetcher, "http://localhost:8000", { timeoutMs: 25 });
    const assertion = expect(request).rejects.toMatchObject({ message: "Dashboard analytics request timed out.", status: 504 });
    await vi.advanceTimersByTimeAsync(25);

    await assertion;
  });

  it("returns an actionable error for malformed dashboard payloads", async () => {
    const fetcher = async () => Response.json({ ...dashboardPayload, prediction_samples: [{ churn_probability: "0.5" }] });

    await expect(fetchDashboardAnalytics(fetcher, "http://localhost:8000")).rejects.toMatchObject({
      message: "Dashboard analytics payload is malformed.",
      status: 502,
    });
  });
});

describe("education wire contract (Phase 3a)", () => {
  it("wire guard accepts an education-shaped payload with all education cohort fields", async () => {
    const fetcher = async () => Response.json(educationPayload);

    const result = await fetchDashboardAnalytics(fetcher, "http://localhost:8000");

    expect(result.artifactVersion).toBe("run-2026-07-07");
    expect(result.predictionSamples).toHaveLength(2);
    const first: PredictionSample = result.predictionSamples[0];
    expect(first.sampleId).toBe("student-001");
    expect(first.displayReference).toBe("Student 001");
    expect(first.churnProbability).toBe(0.88);
    expect(first.majorCategory).toBe("Engineering");
    expect(first.weeklyGenAiHours).toBe(15);
    expect(first.perceivedAiDependency).toBe("High");
    expect(first.institutionalPolicy).toBe("Restrictive");
  });

  it("wire guard rejects a Telco-shaped payload as malformed", async () => {
    const fetcher = async () => Response.json(telcoOnlyPayload);

    await expect(fetchDashboardAnalytics(fetcher, "http://localhost:8000")).rejects.toMatchObject({
      message: "Dashboard analytics payload is malformed.",
      status: 502,
    });
  });

  it("wire guard rejects a payload missing an education field", async () => {
    const incompletePayload = {
      ...educationPayload,
      prediction_samples: [
        {
          sample_id: "student-003",
          display_reference: "Student 003",
          churn_probability: "0.55",
          Major_Category: "Business",
          Weekly_GenAI_Hours: "8",
          Perceived_AI_Dependency: "Medium",
          // Institutional_Policy intentionally missing
        },
      ],
    };
    const fetcher = async () => Response.json(incompletePayload);

    await expect(fetchDashboardAnalytics(fetcher, "http://localhost:8000")).rejects.toMatchObject({
      message: "Dashboard analytics payload is malformed.",
      status: 502,
    });
  });
});
