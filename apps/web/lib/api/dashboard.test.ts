import { afterEach, describe, expect, it, vi } from "vitest";

import { DashboardAnalyticsError, fetchDashboardAnalytics } from "./client";

const dashboardPayload = {
  artifact_version: "run-2026-07-02",
  freshness: { metrics_created_at_utc: "2026-07-02T00:00:00Z" },
  kpis: { pr_auc: 0.82, recall: 0.74 },
  risk_distribution: { high: 2, low: 1 },
  threshold: 0.6,
  prediction_samples: [
    {
      sample_id: "sample-001",
      display_reference: "Sample 001",
      churn_probability: "0.81",
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
    expect(result.artifactVersion).toBe("run-2026-07-02");
    expect(result.threshold).toBe(0.6);
    expect(result.predictionSamples[0]).toMatchObject({
      sampleId: "sample-001",
      displayReference: "Sample 001",
      contract: "Month-to-month",
      tenure: 3,
      monthlyCharges: 91.25,
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
