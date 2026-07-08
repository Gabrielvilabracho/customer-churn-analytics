import type { DashboardAnalytics, PredictionSample } from "@/lib/api/types";

const DEFAULT_RISK_LABEL_THRESHOLD = 0.5;

export interface KpiCardModel {
  label: string;
  value: string;
  detail: string;
}

export interface ContractCohortModel {
  contract: string;
  customers: number;
  averageChurnProbability: string;
  averageMonthlyCharges: string;
}

export interface TopRiskCustomerModel {
  sampleId: string;
  displayReference: string;
  contract: string;
  churnProbability: string;
  riskLabel: string;
  paymentMethod: string;
  internetService: string;
}

export interface ExecutiveDashboardModel {
  artifactVersion: string;
  freshnessLabel: string;
  kpiCards: KpiCardModel[];
  contractCohorts: ContractCohortModel[];
  topRiskCustomers: TopRiskCustomerModel[];
}

export function buildExecutiveDashboardModel(analytics: DashboardAnalytics): ExecutiveDashboardModel {
  const samples = analytics.predictionSamples;
  return {
    artifactVersion: analytics.artifactVersion,
    freshnessLabel: analytics.freshness.metrics_created_at_utc ?? "Freshness unavailable",
    kpiCards: buildKpiCards(analytics),
    contractCohorts: buildContractCohorts(samples),
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
      label: "High-risk customers",
      value: String(analytics.riskDistribution.high ?? 0),
      detail: "From prediction samples",
    },
    buildAverageRiskCard(samples),
  ];
}

function buildAverageRiskCard(samples: PredictionSample[]): KpiCardModel {
  if (samples.length === 0) {
    return {
      label: "Average churn risk",
      value: "No samples",
      detail: "Run the training pipeline to publish prediction rows",
    };
  }

  return {
    label: "Average churn risk",
    value: formatPercent(average(samples.map((sample) => sample.churnProbability))),
    detail: `${samples.length} sampled customers`,
  };
}

function buildContractCohorts(samples: PredictionSample[]): ContractCohortModel[] {
  const cohorts = new Map<string, PredictionSample[]>();
  for (const sample of samples) {
    cohorts.set(sample.contract, [...(cohorts.get(sample.contract) ?? []), sample]);
  }

  return [...cohorts.entries()]
    .map(([contract, rows]) => ({
      contract,
      customers: rows.length,
      averageChurnProbability: formatPercent(average(rows.map((row) => row.churnProbability))),
      averageMonthlyCharges: formatCurrency(average(rows.map((row) => row.monthlyCharges))),
    }))
    .toSorted((left, right) => right.customers - left.customers || left.contract.localeCompare(right.contract));
}

function buildTopRiskCustomers(samples: PredictionSample[], threshold: number): TopRiskCustomerModel[] {
  return samples
    .toSorted((left, right) => right.churnProbability - left.churnProbability)
    .slice(0, 5)
    .map((sample) => ({
      sampleId: sample.sampleId,
      displayReference: sample.displayReference,
      contract: sample.contract,
      churnProbability: formatPercent(sample.churnProbability),
      riskLabel: sample.churnProbability >= threshold ? "High risk" : "Monitor",
      paymentMethod: sample.paymentMethod,
      internetService: sample.internetService,
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

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}
