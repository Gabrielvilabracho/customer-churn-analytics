export interface DashboardFreshness {
  metrics_created_at_utc?: string;
  [key: string]: string | undefined;
}

export interface DashboardKpis {
  pr_auc?: number;
  recall?: number;
  precision?: number;
  accuracy?: number;
  [key: string]: number | undefined;
}

export interface DashboardRiskDistribution {
  high?: number;
  low?: number;
  [key: string]: number | undefined;
}

export interface PredictionSample {
  sampleId: string;
  displayReference: string;
  churnProbability: number;
  majorCategory: string;
  weeklyGenAiHours: number;
  perceivedAiDependency: number | string;
  institutionalPolicy: string;
}

export interface DashboardAnalytics {
  artifactVersion: string;
  freshness: DashboardFreshness;
  kpis: DashboardKpis;
  riskDistribution: DashboardRiskDistribution;
  threshold?: number;
  predictionSamples: PredictionSample[];
}
