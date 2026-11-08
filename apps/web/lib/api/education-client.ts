import type { DashboardFetcher } from "./client";
import { DIRECTION } from "./education-types";
import type { AssociationMeasures, EducationAnalysis } from "./education-types";

function record(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error("Invalid education analysis object.");
  return value as Record<string, unknown>;
}
function text(value: unknown): string {
  if (typeof value !== "string") throw new Error("Invalid education analysis text.");
  return value;
}
function number(value: unknown): number {
  if (typeof value !== "number" || !Number.isFinite(value)) throw new Error("Invalid education analysis number.");
  return value;
}
function nullable(value: unknown): number | null { return value === null ? null : number(value); }
function nullableText(value: unknown): string | null { return value === null ? null : text(value); }
function array(value: unknown): unknown[] {
  if (!Array.isArray(value)) throw new Error("Invalid education analysis list.");
  return value;
}
function rate(value: unknown): number {
  const result = number(value);
  if (result < 0 || result > 1) throw new Error("Invalid education analysis rate.");
  return result;
}
function measures(value: unknown): AssociationMeasures {
  const item = record(value);
  const result: AssociationMeasures = { count: number(item.count), missing_count: number(item.missing_count) };
  for (const key of ["point_biserial", "spearman", "cramers_v"] as const) {
    if (key in item) result[key] = nullable(item[key]);
  }
  return result;
}

export function parseEducationAnalysis(value: unknown): EducationAnalysis {
  const data = record(value);
  if (data.schema_version !== 1 || data.decision_support_only !== true || data.qualified_human_review_required !== true
    || JSON.stringify(data).includes('"Student_ID"')) throw new Error("Incompatible education analysis contract.");
  const summary = record(data.summary);
  const shap = record(data.shap);
  if (shap.units !== "log_odds" || shap.method !== "exact_independent_linear") throw new Error("Unsupported SHAP units or method.");
  const coefficients = array(data.coefficients).map((value) => {
    const item = record(value);
    const direction = text(item.direction);
    if (direction !== DIRECTION.POSITIVE && direction !== DIRECTION.NEGATIVE && direction !== DIRECTION.NEUTRAL) throw new Error("Invalid coefficient direction.");
    return { feature: text(item.feature), term: text(item.term), category: nullableText(item.category),
      coefficient: number(item.coefficient), original_unit_coefficient: nullable(item.original_unit_coefficient),
      odds_ratio: number(item.odds_ratio), direction, unit: text(item.unit), reference: nullableText(item.reference) };
  });
  const importance = array(data.importance).map((value) => {
    const item = record(value);
    return { feature: text(item.feature), mean_abs_shap: number(item.mean_abs_shap),
      permutation_mean: number(item.permutation_mean), permutation_std: number(item.permutation_std) };
  });
  const associations = array(data.associations).map((value) => {
    const item = record(value);
    return { feature: text(item.feature), kind: text(item.kind), train: measures(item.train), test: measures(item.test) };
  });
  const cohorts = array(data.cohorts).map((value) => {
    const item = record(value);
    if (typeof item.suppressed !== "boolean") throw new Error("Invalid cohort suppression.");
    const count = number(item.count);
    const minimum = number(summary.minimum_cohort_size);
    if (!Number.isInteger(count) || count < 1 || !Number.isInteger(minimum) || minimum < 2
      || item.suppressed !== (count < minimum)) throw new Error("Inconsistent cohort suppression.");
    if (item.suppressed && [item.observed_high_rate, item.observed_ci,
      item.average_predicted_risk, item.difference_from_overall, item.precision, item.recall]
      .some((statistic) => statistic !== null)) throw new Error("Small-cohort statistics must be suppressed.");
    const interval = item.observed_ci === null ? null : array(item.observed_ci).map(rate);
    if (interval !== null && interval.length !== 2) throw new Error("Invalid cohort interval.");
    return { feature: text(item.feature), group: text(item.group), count: number(item.count), suppressed: item.suppressed,
      observed_high_rate: nullable(item.observed_high_rate), observed_ci: interval,
      average_predicted_risk: nullable(item.average_predicted_risk), difference_from_overall: nullable(item.difference_from_overall),
      precision: nullable(item.precision), recall: nullable(item.recall) };
  });
  const samples = array(shap.samples).map((value) => {
    const item = record(value);
    const contributions = array(item.contributions).map((value) => {
      const term = record(value);
      return { feature: text(term.feature), value: text(term.value), shap_value: number(term.shap_value) };
    });
    const sample = { sample_id: text(item.sample_id), base_value: number(item.base_value),
      output_value: number(item.output_value), predicted_probability: rate(item.predicted_probability), contributions };
    if (Math.abs(sample.base_value + contributions.reduce((sum, term) => sum + term.shap_value, 0) - sample.output_value) > 1e-7)
      throw new Error("SHAP explanation does not match model output.");
    const probability = sample.output_value >= 0
      ? 1 / (1 + Math.exp(-sample.output_value))
      : Math.exp(sample.output_value) / (1 + Math.exp(sample.output_value));
    if (Math.abs(probability - sample.predicted_probability) > 1e-7)
      throw new Error("SHAP explanation does not match model probability.");
    return sample;
  });
  const modelMetrics: Record<string, number> = {};
  for (const [key, value] of Object.entries(record(data.model_metrics))) modelMetrics[key] = number(value);
  return {
    run_id: text(data.run_id), analysis_id: text(data.analysis_id), dataset_id: text(data.dataset_id),
    model_name: text(data.model_name), created_at_utc: text(data.created_at_utc),
    summary: { train_count: number(summary.train_count), test_count: number(summary.test_count),
      threshold: rate(summary.threshold), observed_high_rate: rate(summary.observed_high_rate),
      average_predicted_risk: rate(summary.average_predicted_risk), minimum_cohort_size: number(summary.minimum_cohort_size) },
    coefficients, importance, associations, cohorts, model_metrics: modelMetrics,
    shap: { units: text(shap.units), background_count: number(shap.background_count),
      sample_count: number(shap.sample_count), samples },
    warnings: array(data.warnings).map(text),
  };
}

export async function fetchEducationAnalysis(
  fetcher: DashboardFetcher = fetch, baseUrl = "http://127.0.0.1:8000", scenario?: string,
): Promise<EducationAnalysis> {
  const url = new URL("/analytics/education", baseUrl);
  if (scenario) url.searchParams.set("scenario", scenario);
  const response = await fetcher(url.toString(), { cache: "no-store", signal: AbortSignal.timeout(10_000) });
  const data: unknown = await response.json();
  if (!response.ok) {
    const payload = record(data);
    throw new Error(typeof payload.reason === "string" ? payload.reason : "Education analysis is unavailable.");
  }
  return parseEducationAnalysis(data);
}
