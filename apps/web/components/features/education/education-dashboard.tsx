"use client";

import { useState } from "react";
import type { EducationAnalysis } from "@/lib/api/education-types";
import { decimal, DependencyChart, ImportanceChart, label, percent, ShapDistribution, Waterfall } from "./charts";
import styles from "./education.module.css";

const VIEW = { OVERVIEW: "Overview", VARIABLES: "Variables", COHORTS: "Cohorts", EXPLANATIONS: "Explanations" } as const;
type View = (typeof VIEW)[keyof typeof VIEW];

export function EducationDashboard({ analysis }: { analysis: EducationAnalysis }) {
  const features = analysis.importance.map((item) => item.feature);
  const [view, setView] = useState<View>(VIEW.VARIABLES);
  const [feature, setFeature] = useState(features[0] ?? "");
  const [cohortFeature, setCohortFeature] = useState(features.includes("Major_Category") ? "Major_Category" : features[0] ?? "");
  const [sampleId, setSampleId] = useState(analysis.shap.samples[0]?.sample_id ?? "");
  const sample = analysis.shap.samples.find((sample) => sample.sample_id === sampleId);
  const association = analysis.associations.find((row) => row.feature === feature);
  const cohortRows = analysis.cohorts.filter((row) => row.feature === cohortFeature);
  return <main className={styles.page}>
    <div className={styles.shell}>
      <header className={styles.header}>
        <div><p className={styles.eyebrow}>Education research / model inspection</p>
          <h1>Burnout &amp; AI study</h1>
          <p className={styles.lead}>Explore what the model learned, what the data shows, and where uncertainty remains.</p>
        </div>
        <div className={styles.identity}><span>Analysis publication</span><strong>{analysis.analysis_id}</strong>
          <span>Model run: {analysis.run_id}</span><span>{analysis.created_at_utc}</span></div>
      </header>
      <aside className={styles.notice}>Decision support only. Qualified human review is required. Predictions must not determine grading, discipline, enrollment or access to student services.</aside>
      <dl className={styles.summary}>
        <div><dt>Training / held-out students</dt><dd>{analysis.summary.train_count.toLocaleString("en-US")} / {analysis.summary.test_count.toLocaleString("en-US")}</dd></div>
        <div><dt>Observed high burnout</dt><dd>{percent(analysis.summary.observed_high_rate)}</dd></div>
        <div><dt>Average predicted risk</dt><dd>{percent(analysis.summary.average_predicted_risk)}</dd></div>
        <div><dt>Positive target</dt><dd>High <small>vs. Low + Medium</small></dd></div>
      </dl>
      <nav className={styles.navigation} aria-label="Analysis views">
        {Object.values(VIEW).map((item) => <button key={item} type="button" aria-pressed={view === item} onClick={() => setView(item)}>{item}</button>)}
      </nav>
      {view === VIEW.OVERVIEW ? <section className={styles.panel} aria-labelledby="overview-title">
        <p className={styles.eyebrow}>01 / Evaluation context</p><h2 id="overview-title">Read the evidence before the ranking</h2>
        <p>These are held-out associations and model explanations, not evidence that AI use causes burnout. A high predicted score is not a diagnosis.</p>
        <dl className={styles.metrics}>{Object.entries(analysis.model_metrics).map(([metric, value]) => <div key={metric}><dt>{label(metric)}</dt><dd>{decimal(value)}</dd></div>)}</dl>
        <p>Selected decision threshold: {decimal(analysis.summary.threshold)}. Class balancing can change probability calibration; observed prevalence and predicted risk are different quantities.</p>
        <h3>Method and limitations</h3><ul>{analysis.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
        <p>Model: {analysis.model_name}. Dataset: {analysis.dataset_id}. Numeric cohorts use training-set quartiles. SHAP uses {analysis.shap.background_count.toLocaleString("en-US")} training rows and {analysis.shap.sample_count} held-out explanations.</p>
      </section> : null}
      {view === VIEW.VARIABLES ? <section className={styles.panel} aria-labelledby="variables-title">
        <div className={styles.sectionHeader}><div><p className={styles.eyebrow}>02 / Model and data</p><h2 id="variables-title">Variables, not verdicts</h2></div>
          <label className={styles.control}>Variable to inspect<select value={feature} onChange={(e) => setFeature(e.target.value)}>{features.map((name) => <option key={name} value={name}>{label(name)}</option>)}</select></label>
        </div>
        {!features.length ? <p>No variable analysis is available.</p> : <>
          <div className={styles.twoColumns}><ImportanceChart rows={analysis.importance} /><DependencyChart samples={analysis.shap.samples} feature={feature} /></div>
          <h3>Fitted effects: {label(feature)}</h3>
          <p>Positive coefficients increase model log-odds of High burnout; negative coefficients reduce them, holding other inputs fixed. Numeric odds ratios are per training standard deviation, not percentage-point risk changes. Category effects are explicit contrasts with the named reference.</p>
          <div className={styles.tableScroll}><table><caption>Interpreted coefficients</caption><thead><tr><th scope="col">Term</th><th scope="col">Coefficient</th><th scope="col">Odds ratio</th><th scope="col">Direction</th><th scope="col">Units / reference</th></tr></thead>
            <tbody>{analysis.coefficients.filter((r) => r.feature === feature).map((r) => <tr key={r.term}><th scope="row">{r.category ?? label(r.feature)}</th><td>{decimal(r.coefficient)}</td><td>{decimal(r.odds_ratio)}</td><td>{r.direction}</td><td>{r.unit}{r.reference ? ` vs. ${r.reference}` : `; original-unit coefficient ${decimal(r.original_unit_coefficient)}`}</td></tr>)}</tbody></table></div>
          <h3>Association is not the same as model importance</h3>
          <div className={styles.tableScroll}><table><caption>Train / held-out associations for {label(feature)}</caption><thead><tr><th scope="col">Measure</th><th scope="col">Training</th><th scope="col">Held-out</th></tr></thead><tbody>
            {association ? (association.kind === "numeric" ? ["point_biserial", "spearman"] as const : ["cramers_v"] as const).map((key) => <tr key={key}><th scope="row">{label(key)}</th><td>{decimal(association.train[key])}</td><td>{decimal(association.test[key])}</td></tr>) : null}
          </tbody></table></div>
          <p>Cramér’s V measures association strength, not direction. Undefined values indicate constant inputs or an unidentifiable association.</p>
          <div className={styles.tableScroll}><table><caption>Held-out permutation importance (drop in average precision; five repeats)</caption><thead><tr><th scope="col">Variable</th><th scope="col">Mean drop</th><th scope="col">Standard deviation</th><th scope="col">Mean |SHAP|</th></tr></thead><tbody>
            {analysis.importance.toSorted((a, b) => b.permutation_mean - a.permutation_mean).map((r) => <tr key={r.feature}><th scope="row">{label(r.feature)}</th><td>{decimal(r.permutation_mean)}</td><td>{decimal(r.permutation_std)}</td><td>{decimal(r.mean_abs_shap)}</td></tr>)}
          </tbody></table></div>
          <p>Negative permutation importance is retained, not clipped. Correlated predictors can dilute importance rankings.</p>
        </>}
      </section> : null}
      {view === VIEW.COHORTS ? <section className={styles.panel} aria-labelledby="cohorts-title">
        <div className={styles.sectionHeader}><div><p className={styles.eyebrow}>03 / Group comparisons</p><h2 id="cohorts-title">Observed outcomes, predicted risks</h2></div>
          <label className={styles.control}>Cohort variable<select value={cohortFeature} onChange={(e) => setCohortFeature(e.target.value)}>{features.map((name) => <option key={name} value={name}>{label(name)}</option>)}</select></label>
        </div>
        <p>Held-out students only. Error ranges are 95% Wilson intervals for observed High burnout. Statistics are suppressed below {analysis.summary.minimum_cohort_size} students; these are not intervention effects.</p>
        {!cohortRows.length ? <p>No cohort comparisons are available.</p> : <div className={styles.tableScroll}><table><caption>{label(cohortFeature)} cohort comparison</caption><thead><tr><th scope="col">Group</th><th scope="col">Students</th><th scope="col">Observed high burnout</th><th scope="col">95% interval</th><th scope="col">Predicted risk</th><th scope="col">Precision</th><th scope="col">Recall</th></tr></thead><tbody>
          {cohortRows.map((r) => <tr key={r.group}><th scope="row">{r.group}</th><td>{r.count}</td><td>{percent(r.observed_high_rate, r.suppressed)}</td><td>{r.suppressed ? "Suppressed" : r.observed_ci ? `${percent(r.observed_ci[0])} to ${percent(r.observed_ci[1])}` : "Undefined"}</td><td>{percent(r.average_predicted_risk, r.suppressed)}</td><td>{percent(r.precision, r.suppressed)}</td><td>{percent(r.recall, r.suppressed)}</td></tr>)}
        </tbody></table></div>}
      </section> : null}
      {view === VIEW.EXPLANATIONS ? <section className={styles.panel} aria-labelledby="explanations-title">
        <p className={styles.eyebrow}>04 / Independent linear SHAP</p><h2 id="explanations-title">What moved the model output?</h2>
        <p>Contributions sum in log-odds. Apply the logistic function only after adding the base value and all contributions. They are not additive probability changes.</p>
        {analysis.shap.samples.length ? <>
          <ShapDistribution samples={analysis.shap.samples} features={features} />
          <label className={styles.control}>Anonymized held-out sample<select value={sampleId} onChange={(e) => setSampleId(e.target.value)}>{analysis.shap.samples.map((s) => <option key={s.sample_id} value={s.sample_id}>{s.sample_id}</option>)}</select></label>
          {sample ? <><p className={styles.prediction}>Model probability <strong>{percent(sample.predicted_probability)}</strong><span>Not a calibrated diagnosis</span></p>
            <Waterfall sample={sample} />
            <div className={styles.tableScroll}><table><caption>Signed contributions for {sample.sample_id}</caption><thead><tr><th scope="col">Variable</th><th scope="col">Value</th><th scope="col">SHAP (log-odds)</th></tr></thead><tbody>{sample.contributions.map((r) => <tr key={r.feature}><th scope="row">{label(r.feature)}</th><td>{r.value}</td><td>{decimal(r.shap_value)}</td></tr>)}</tbody></table></div>
          </> : null}
        </> : <p>No held-out explanations are available.</p>}
      </section> : null}
      <footer className={styles.footer}>Reproducible local analysis. No live surveillance. No automatic student decisions. <a href="/">Legacy dashboard</a></footer>
    </div>
  </main>;
}
