import type { DashboardAnalytics, PredictionSample } from "@/lib/api/types";

const DEFAULT_RISK_LABEL_THRESHOLD = 0.5;

export interface KpiCardModel {
  label: string;
  value: string;
  detail: string;
}

export interface MajorCategoryCohortModel {
  majorCategory: string;
  customers: number;
  averageChurnProbability: string;
}

export interface TopRiskCustomerModel {
  sampleId: string;
  displayReference: string;
  majorCategory: string;
  churnProbability: string;
  riskLabel: string;
  weeklyGenAiHours: string;
  perceivedAiDependency: string;
  institutionalPolicy: string;
}

export interface ExecutiveDashboardModel {
  artifactVersion: string;
  freshnessLabel: string;
  kpiCards: KpiCardModel[];
  majorCategoryCohorts: MajorCategoryCohortModel[];
  topRiskCustomers: TopRiskCustomerModel[];
}

export function buildExecutiveDashboardModel(analytics: DashboardAnalytics): ExecutiveDashboardModel {
  const samples = analytics.predictionSamples;
  return {
    artifactVersion: analytics.artifactVersion,
    freshnessLabel: analytics.freshness.metrics_created_at_utc ?? "Freshness unavailable",
    kpiCards: buildKpiCards(analytics),
    majorCategoryCohorts: buildMajorCategoryCohorts(samples),
    topRiskCustomers: buildTopRiskCustomers(samples, analytics.threshold ?? DEFAULT_RISK_LABEL_THRESHOLD),
  };
}

function buildKpiCards(analytics: DashboardAnalytics): KpiCardModel[] {
  const samples = analytics.predictionSamples;
  return [
    {
      label: "Model PR-AUC",
      value: formatDecimal(analytics.kpis.pr_auc),
      detail: analytics.artifactVersion,
    },
    {
      label: "Recall",
      value: formatPercent(analytics.kpis.recall),
      detail: "At selected threshold",
    },
    {
      label: "High-risk students",
      value: String(analytics.riskDistribution.high ?? 0),
      detail: "From prediction samples",
    },
    buildAverageRiskCard(samples),
  ];
}

function buildAverageRiskCard(samples: PredictionSample[]): KpiCardModel {
  if (samples.length === 0) {
    return {
      label: "Average burnout risk",
      value: "No samples",
      detail: "Run the training pipeline to publish prediction rows",
    };
  }

  return {
    label: "Average burnout risk",
    value: formatPercent(average(samples.map((sample) => sample.churnProbability))),
    detail: `${samples.length} sampled students`,
  };
}

function buildMajorCategoryCohorts(samples: PredictionSample[]): MajorCategoryCohortModel[] {
  const cohorts = new Map<string, PredictionSample[]>();
  for (const sample of samples) {
    cohorts.set(sample.majorCategory, [...(cohorts.get(sample.majorCategory) ?? []), sample]);
  }

  return [...cohorts.entries()]
    .map(([majorCategory, rows]) => ({
      majorCategory,
      customers: rows.length,
      averageChurnProbability: formatPercent(average(rows.map((row) => row.churnProbability))),
    }))
    .toSorted((left, right) => right.customers - left.customers || left.majorCategory.localeCompare(right.majorCategory));
}

function buildTopRiskCustomers(samples: PredictionSample[], threshold: number): TopRiskCustomerModel[] {
  return samples
    .toSorted((left, right) => right.churnProbability - left.churnProbability)
    .slice(0, 5)
    .map((sample) => ({
      sampleId: sample.sampleId,
      displayReference: sample.displayReference,
      majorCategory: sample.majorCategory,
      churnProbability: formatPercent(sample.churnProbability),
      riskLabel: sample.churnProbability >= threshold ? "High risk" : "Monitor",
      weeklyGenAiHours: String(sample.weeklyGenAiHours),
      perceivedAiDependency: String(sample.perceivedAiDependency),
      institutionalPolicy: sample.institutionalPolicy,
    }));
}

function average(values: number[]): number {
  if (values.length === 0) {
    return 0;
  }
  return values.reduce((total, value) => total + value, 0) / values.length;
}

function formatDecimal(value: number | undefined): string {
  return value === undefined ? "N/A" : value.toFixed(2);
}

function formatPercent(value: number | undefined): string {
  return value === undefined ? "N/A" : `${Math.round(value * 100)}%`;
}
