import type { Importance, ShapSample } from "@/lib/api/education-types";
import styles from "./education.module.css";

export function label(feature: string): string { return feature.replaceAll("_", " "); }
export function decimal(value: number | null | undefined): string { return value == null ? "Undefined" : value.toFixed(3); }
export function percent(value: number | null | undefined, suppressed = false): string {
  if (suppressed) return "Suppressed";
  return value == null ? "Undefined" : `${(value * 100).toFixed(1)}%`;
}

export function ImportanceChart({ rows }: { rows: Importance[] }) {
  const sorted = rows.toSorted((a, b) => b.mean_abs_shap - a.mean_abs_shap);
  const max = Math.max(...sorted.map((r) => r.mean_abs_shap), 0.001);
  return <figure className={styles.figure}>
    <figcaption>Global importance <span>Mean |SHAP|, log-odds. No direction implied.</span></figcaption>
    <svg role="img" aria-label="Global variable importance" viewBox={`0 0 680 ${sorted.length * 32 + 24}`}>
      <title>Mean absolute grouped SHAP contributions on held-out samples</title>
      {sorted.map((row, i) => <g key={row.feature}>
        <text x="0" y={i * 32 + 20} fontSize="12">{label(row.feature)}</text>
        <rect x="240" y={i * 32 + 6} width={row.mean_abs_shap / max * 340} height="18" rx="2" className={styles.importanceBar} />
        <text x="600" y={i * 32 + 20} fontSize="12">{decimal(row.mean_abs_shap)}</text>
      </g>)}
    </svg>
  </figure>;
}

export function ShapDistribution({ samples, features }: { samples: ShapSample[]; features: string[] }) {
  const max = Math.max(...samples.flatMap((s) => s.contributions.map((c) => Math.abs(c.shap_value))), 0.01);
  const x = (value: number) => 440 + value / max * 190;
  return <figure className={styles.figure}>
    <figcaption>Held-out contribution distribution <span>Each point is an anonymized sample; jitter is for visibility only.</span></figcaption>
    <svg role="img" aria-label="SHAP contribution distribution" viewBox={`0 0 680 ${features.length * 32 + 42}`}>
      <title>Independent linear SHAP distribution, negative to positive log-odds contributions</title>
      <line x1="440" x2="440" y1="0" y2={features.length * 32} className={styles.axis} />
      {features.map((feature, row) => <g key={feature}>
        <text x="0" y={row * 32 + 20} fontSize="12">{label(feature)}</text>
        {samples.map((sample, index) => {
          const contribution = sample.contributions.find((c) => c.feature === feature);
          if (!contribution) return null;
          return <circle key={sample.sample_id} cx={x(contribution.shap_value)} cy={row * 32 + 16 + ((index * 7) % 13 - 6)}
            r="2.5" opacity="0.5" className={contribution.shap_value < 0 ? styles.negative : styles.positive}>
            <title>{`${sample.sample_id}: ${label(feature)} = ${contribution.value}, SHAP ${decimal(contribution.shap_value)}`}</title>
          </circle>;
        })}
      </g>)}
      <text x="245" y={features.length * 32 + 25} fontSize="12">−{decimal(max)}</text>
      <text x="435" y={features.length * 32 + 25} fontSize="12">0</text>
      <text x="590" y={features.length * 32 + 25} fontSize="12">+{decimal(max)}</text>
    </svg>
  </figure>;
}

export function DependencyChart({ samples, feature }: { samples: ShapSample[]; feature: string }) {
  const rows = samples.flatMap((sample) => {
    const term = sample.contributions.find((c) => c.feature === feature);
    return term ? [term] : [];
  });
  if (!rows.length) return <p>No dependency samples are available.</p>;
  const numeric = rows.every((r) => Number.isFinite(Number(r.value)));
  const categories = [...new Set(rows.map((r) => r.value))].sort();
  const values = rows.map((r) => numeric ? Number(r.value) : categories.indexOf(r.value));
  const low = Math.min(...values);
  const high = Math.max(...values);
  const limit = Math.max(...rows.map((r) => Math.abs(r.shap_value)), 0.01);
  return <figure className={styles.figure}>
    <figcaption>Value and contribution <span>{label(feature)}. This is a model relationship, not a causal curve.</span></figcaption>
    <svg role="img" aria-label={`SHAP dependency for ${label(feature)}`} viewBox="0 0 680 220">
      <title>Feature values on the horizontal axis and signed SHAP log-odds on the vertical axis</title>
      <line x1="48" x2="640" y1="100" y2="100" className={styles.axis} />
      {rows.map((r, index) => <circle key={index} cx={48 + (values[index] - low) / (high - low || 1) * 580}
        cy={100 - r.shap_value / limit * 72} r="3" opacity="0.6" className={r.shap_value < 0 ? styles.negative : styles.positive}>
        <title>{`${r.value}: ${decimal(r.shap_value)} log-odds`}</title>
      </circle>)}
      <text x="0" y="30" fontSize="11">+{decimal(limit)}</text>
      <text x="0" y="180" fontSize="11">−{decimal(limit)}</text>
      <text x="48" y="205" fontSize="11">{numeric ? low : categories[0]}</text>
      <text x="640" y="205" fontSize="11" textAnchor="end">{numeric ? high : categories.at(-1)}</text>
    </svg>
  </figure>;
}

export function Waterfall({ sample }: { sample: ShapSample }) {
  let cursor = sample.base_value;
  const steps = sample.contributions.toSorted((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value)).map((term) => {
    const start = cursor;
    cursor += term.shap_value;
    return { ...term, start, end: cursor };
  });
  const minimum = Math.min(sample.base_value, ...steps.map((s) => Math.min(s.start, s.end)));
  const maximum = Math.max(sample.base_value, ...steps.map((s) => Math.max(s.start, s.end)));
  const x = (value: number) => 240 + (value - minimum) / (maximum - minimum || 1) * 350;
  return <figure className={styles.figure}>
    <figcaption>From background to prediction <span>Base {decimal(sample.base_value)} → output {decimal(sample.output_value)} log-odds.</span></figcaption>
    <svg role="img" aria-label={`SHAP waterfall for ${sample.sample_id}`} viewBox={`0 0 680 ${steps.length * 34 + 34}`}>
      <title>Signed cumulative contributions in log-odds, not probability increments</title>
      {steps.map((term, i) => <g key={term.feature}>
        <text x="0" y={i * 34 + 22} fontSize="12">{label(term.feature)}</text>
        <rect x={x(Math.min(term.start, term.end))} y={i * 34 + 8}
          width={Math.max(1, Math.abs(x(term.end) - x(term.start)))} height="19" rx="2"
          className={term.shap_value < 0 ? styles.negative : styles.positive} />
        <text x="610" y={i * 34 + 22} fontSize="12">{term.shap_value >= 0 ? "+" : ""}{decimal(term.shap_value)}</text>
        <line x1={x(term.end)} x2={x(term.end)} y1={i * 34 + 27} y2={(i + 1) * 34 + 8} className={styles.axis} />
      </g>)}
    </svg>
  </figure>;
}
