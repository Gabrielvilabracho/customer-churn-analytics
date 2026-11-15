import { describe, expect, it } from "vitest";
import fixture from "../../e2e/fixtures/education.json";
import { fetchEducationAnalysis, parseEducationAnalysis } from "./education-client";
import { percent } from "../../components/features/education/charts";

describe("education analysis contract", () => {
  it("reads the versioned analysis and signed explanations", () => {
    const data = parseEducationAnalysis(fixture);
    expect(data.run_id).toBe("synthetic-education-run");
    expect(data.coefficients[0].direction).toBe("positive");
    expect(data.shap.samples[1].contributions[0].shap_value).toBeLessThan(0);
  });

  it("rejects incompatible, nonfinite and unsafe education responses", () => {
    expect(() => parseEducationAnalysis({ ...fixture, schema_version: 2 })).toThrow();
    expect(() => parseEducationAnalysis({ ...fixture, decision_support_only: false })).toThrow();
    expect(() => parseEducationAnalysis({ ...fixture, coefficients: [{ coefficient: NaN }] })).toThrow();
    expect(() => parseEducationAnalysis({ ...fixture, Student_ID: "private" })).toThrow();
    expect(() => parseEducationAnalysis({ ...fixture, shap: { ...fixture.shap, units: "probability" } })).toThrow();
  });

  it("requests the additive endpoint without caching and preserves degraded reasons", async () => {
    const calls: string[] = [];
    await fetchEducationAnalysis(async (url, init) => {
      calls.push(url);
      expect(init?.cache).toBe("no-store");
      return new Response(JSON.stringify(fixture));
    }, "http://127.0.0.1:8000");
    expect(calls).toEqual(["http://127.0.0.1:8000/analytics/education"]);
    await expect(fetchEducationAnalysis(async () => new Response(
      JSON.stringify({ reason: "Analysis source binding is stale" }), { status: 503 },
    ))).rejects.toThrow("Analysis source binding is stale");
  });

  it("does not fabricate values for empty arrays", () => {
    const empty = parseEducationAnalysis({ ...fixture, coefficients: [], importance: [],
      associations: [], cohorts: [], shap: { ...fixture.shap, samples: [], sample_count: 0 } });
    expect(empty.importance).toEqual([]);
    expect(empty.shap.samples).toEqual([]);
  });

  it("rejects probabilities inconsistent with the explained log-odds", () => {
    const changed = structuredClone(fixture);
    changed.shap.samples[1].predicted_probability = 0.99;
    expect(() => parseEducationAnalysis(changed)).toThrow();
  });

  it.each(["populated", "small-visible", "large-suppressed"])(
    "rejects inconsistent cohort suppression: %s", (caseName) => {
      const changed = structuredClone(fixture);
      if (caseName === "populated") changed.cohorts[2].precision = 0.5;
      if (caseName === "small-visible") changed.cohorts[2].suppressed = false;
      if (caseName === "large-suppressed") changed.cohorts[0].suppressed = true;
      expect(() => parseEducationAnalysis(changed)).toThrow();
    },
  );

  it("distinguishes undefined metrics from policy-suppressed statistics", () => {
    expect(percent(null)).toBe("Undefined");
    expect(percent(null, true)).toBe("Suppressed");
    expect(percent(0.6)).toBe("60.0%");
    const changed = structuredClone(fixture);
    changed.cohorts[0].precision = null;
    changed.cohorts[0].recall = null;
    expect(parseEducationAnalysis(changed).cohorts[0].suppressed).toBe(false);
  });

  it("preserves input while enforcing every suppressed statistic and the exact size boundary", () => {
    for (const count of [1, 19, 20, 21]) {
      const changed = structuredClone(fixture);
      changed.cohorts[2].count = count;
      changed.cohorts[2].suppressed = count < changed.summary.minimum_cohort_size;
      const before = JSON.stringify(changed);
      expect(parseEducationAnalysis(changed).cohorts[2].suppressed).toBe(count < 20);
      expect(JSON.stringify(changed)).toBe(before);
    }
    for (const field of ["observed_high_rate", "average_predicted_risk",
      "difference_from_overall", "precision", "recall"] as const) {
      const changed = structuredClone(fixture);
      changed.cohorts[2][field] = 0;
      const before = JSON.stringify(changed);
      expect(() => parseEducationAnalysis(changed)).toThrow("Small-cohort statistics must be suppressed.");
      expect(JSON.stringify(changed)).toBe(before);
    }
    const changed = structuredClone(fixture);
    changed.cohorts[2].observed_ci = [0, 1];
    const before = JSON.stringify(changed);
    expect(() => parseEducationAnalysis(changed)).toThrow("Small-cohort statistics must be suppressed.");
    expect(JSON.stringify(changed)).toBe(before);
  });
});
