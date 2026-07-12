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
    sample("student-001", "Student 001", 0.81, "Engineering", 15, "High", "Restrictive"),
    sample("student-002", "Student 002", 0.43, "Arts", 4, "Low", "Permissive"),
    sample("student-003", "Student 003", 0.16, "Business", 2, "Low", "Permissive"),
  ],
};

describe("buildExecutiveDashboardModel", () => {
  it("derives executive KPIs and major category cohorts from enriched prediction samples", () => {
    const model = buildExecutiveDashboardModel(analytics);

    expect(model.kpiCards).toContainEqual({ label: "Model PR-AUC", value: "0.82", detail: "run-2026-07-02" });
    expect(model.kpiCards).toContainEqual({ label: "Average burnout risk", value: "47%", detail: "3 sampled students" });
    expect(model.majorCategoryCohorts).toEqual([
      { majorCategory: "Arts", customers: 1, averageChurnProbability: "43%" },
      { majorCategory: "Business", customers: 1, averageChurnProbability: "16%" },
      { majorCategory: "Engineering", customers: 1, averageChurnProbability: "81%" },
    ]);
    expect(model.topRiskCustomers[0]).toMatchObject({ displayReference: "Student 001", riskLabel: "High risk", churnProbability: "81%" });
  });

  it("returns an empty-state model when no prediction samples exist", () => {
    const model = buildExecutiveDashboardModel({ ...analytics, riskDistribution: {}, predictionSamples: [] });

    expect(model.kpiCards.at(-1)).toEqual({
      label: "Average burnout risk",
      value: "No samples",
      detail: "Run the training pipeline to publish prediction rows",
    });
    expect(model.majorCategoryCohorts).toEqual([]);
    expect(model.topRiskCustomers).toEqual([]);
  });

  it("labels student risk from the artifact threshold when present", () => {
    const model = buildExecutiveDashboardModel({ ...analytics, threshold: 0.9 });

    expect(model.topRiskCustomers[0]).toMatchObject({ displayReference: "Student 001", riskLabel: "Monitor", churnProbability: "81%" });
  });
});

function sample(
  sampleId: string,
  displayReference: string,
  churnProbability: number,
  majorCategory: string,
  weeklyGenAiHours: number,
  perceivedAiDependency: string,
  institutionalPolicy: string,
) {
  return { sampleId, displayReference, churnProbability, majorCategory, weeklyGenAiHours, perceivedAiDependency, institutionalPolicy };
}
