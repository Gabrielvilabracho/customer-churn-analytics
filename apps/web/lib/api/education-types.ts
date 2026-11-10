export const DIRECTION = { POSITIVE: "positive", NEGATIVE: "negative", NEUTRAL: "neutral" } as const;
export type Direction = (typeof DIRECTION)[keyof typeof DIRECTION];

export interface EducationSummary {
  train_count: number;
  test_count: number;
  threshold: number;
  observed_high_rate: number;
  average_predicted_risk: number;
  minimum_cohort_size: number;
}

export interface Coefficient {
  feature: string;
  term: string;
  category: string | null;
  coefficient: number;
  original_unit_coefficient: number | null;
  odds_ratio: number;
  direction: Direction;
  unit: string;
  reference: string | null;
}

export interface Importance {
  feature: string;
  mean_abs_shap: number;
  permutation_mean: number;
  permutation_std: number;
}

export interface AssociationMeasures {
  count: number;
  missing_count: number;
  point_biserial?: number | null;
  spearman?: number | null;
  cramers_v?: number | null;
}

export interface Association {
  feature: string;
  kind: string;
  train: AssociationMeasures;
  test: AssociationMeasures;
}

export interface Cohort {
  feature: string;
  group: string;
  count: number;
  suppressed: boolean;
  observed_high_rate: number | null;
  observed_ci: number[] | null;
  average_predicted_risk: number | null;
  difference_from_overall: number | null;
  precision: number | null;
  recall: number | null;
}

export interface ShapContribution {
  feature: string;
  value: string;
  shap_value: number;
}

export interface ShapSample {
  sample_id: string;
  base_value: number;
  output_value: number;
  predicted_probability: number;
  contributions: ShapContribution[];
}

export interface ShapAnalysis {
  units: string;
  background_count: number;
  sample_count: number;
  samples: ShapSample[];
}

export interface EducationAnalysis {
  run_id: string;
  analysis_id: string;
  dataset_id: string;
  model_name: string;
  created_at_utc: string;
  summary: EducationSummary;
  model_metrics: Record<string, number>;
  coefficients: Coefficient[];
  importance: Importance[];
  associations: Association[];
  cohorts: Cohort[];
  shap: ShapAnalysis;
  warnings: string[];
}
