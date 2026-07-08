import { describe, expect, it } from "vitest";

import { buildExecutiveDashboardModel } from "./dashboard-model";
import type { DashboardAnalytics } from "@/lib/api/types";

const analytics: DashboardAnalytics = {
  artifactVersion: "run-2026-07-02",
  freshness: { metrics_created_at_utc: "2026-07-02T00:00:00Z" },
  kpis: { pr_auc: 0.82, recall: 0.74, precision: 0.61 },
  riskDistribution: { high: 2, low: 1 },
  threshold: 0.5,
  predictionSamples: [
    sample("sample-001", "Sample 001", 0.81, "Month-to-month", 91.25, "Electronic check", "Fiber optic", 3),
    sample("sample-002", "Sample 002", 0.43, "Month-to-month", 72.75, "Mailed check", "DSL", 9),
    sample("sample-003", "Sample 003", 0.16, "Two year", 42, "Credit card", "DSL", 52),
  ],
};

describe("buildExecutiveDashboardModel", () => {
  it("derives executive KPIs and contract cohorts from enriched prediction samples", () => {
    const model = buildExecutiveDashboardModel(analytics);

    expect(model.kpiCards).toContainEqual({ label: "Model PR-AUC", value: "0.82", detail: "run-2026-07-02" });
    expect(model.kpiCards).toContainEqual({ label: "Average churn risk", value: "47%", detail: "3 sampled customers" });
    expect(model.contractCohorts).toEqual([
      { contract: "Month-to-month", customers: 2, averageChurnProbability: "62%", averageMonthlyCharges: "$82.00" },
      { contract: "Two year", customers: 1, averageChurnProbability: "16%", averageMonthlyCharges: "$42.00" },
    ]);
    expect(model.topRiskCustomers[0]).toMatchObject({ displayReference: "Sample 001", riskLabel: "High risk", churnProbability: "81%" });
  });

  it("returns an empty-state model when no prediction samples exist", () => {
    const model = buildExecutiveDashboardModel({ ...analytics, riskDistribution: {}, predictionSamples: [] });

    expect(model.kpiCards.at(-1)).toEqual({
      label: "Average churn risk",
      value: "No samples",
      detail: "Run the training pipeline to publish prediction rows",
    });
    expect(model.contractCohorts).toEqual([]);
    expect(model.topRiskCustomers).toEqual([]);
  });

  it("labels customer risk from the artifact threshold when present", () => {
    const model = buildExecutiveDashboardModel({ ...analytics, threshold: 0.9 });

    expect(model.topRiskCustomers[0]).toMatchObject({ displayReference: "Sample 001", riskLabel: "Monitor", churnProbability: "81%" });
  });
});

function sample(sampleId: string, displayReference: string, churnProbability: number, contract: string, monthlyCharges: number, paymentMethod: string, internetService: string, tenure: number) {
  return { sampleId, displayReference, churnProbability, contract, monthlyCharges, paymentMethod, internetService, tenure };
}
