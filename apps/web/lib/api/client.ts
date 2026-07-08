import type { DashboardAnalytics, PredictionSample } from "./types";

export type DashboardFetcher = (input: string, init?: RequestInit) => Promise<Response>;

interface DashboardFetchOptions {
  timeoutMs?: number;
  dashboardScenario?: string;
}

interface DashboardAnalyticsWireResponse {
  artifact_version: string;
  freshness: Record<string, string>;
  kpis: Record<string, number>;
  risk_distribution: Record<string, number>;
  threshold?: number;
  prediction_samples: DashboardPredictionSampleWire[];
}

interface DashboardPredictionSampleWire {
  sample_id: string;
  display_reference: string;
  churn_probability: string | number;
  Contract: string;
  tenure: string | number;
  PaymentMethod: string;
  MonthlyCharges: string | number;
  InternetService: string;
}

interface DegradedDashboardResponse {
  reason?: string;
}

export class DashboardAnalyticsError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "DashboardAnalyticsError";
    this.status = status;
  }
}

export async function fetchDashboardAnalytics(
  fetcher: DashboardFetcher = fetch,
  apiBaseUrl = process.env.CHURN_API_BASE_URL ?? "http://localhost:8000",
  options: DashboardFetchOptions = {},
): Promise<DashboardAnalytics> {
  const endpoint = new URL("/analytics/dashboard", apiBaseUrl);
  if (options.dashboardScenario) {
    endpoint.searchParams.set("scenario", options.dashboardScenario);
  }
  const timeoutMs = options.timeoutMs ?? 5_000;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  let response: Response;
  try {
    response = await fetcher(endpoint.toString(), { cache: "no-store", signal: controller.signal });
  } catch (error) {
    if (controller.signal.aborted) {
      throw new DashboardAnalyticsError("Dashboard analytics request timed out.", 504);
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
  const payload: unknown = await response.json();

  if (!response.ok) {
    throw new DashboardAnalyticsError(resolveDegradedReason(payload), response.status);
  }

  return mapDashboardAnalytics(payload);
}

function mapDashboardAnalytics(payload: unknown): DashboardAnalytics {
  if (!isDashboardAnalyticsWireResponse(payload)) {
    throw new DashboardAnalyticsError("Dashboard analytics payload is malformed.", 502);
  }

  return {
    artifactVersion: payload.artifact_version,
    freshness: payload.freshness,
    kpis: payload.kpis,
    riskDistribution: payload.risk_distribution,
    threshold: payload.threshold,
    predictionSamples: payload.prediction_samples.map(mapPredictionSample),
  };
}

function mapPredictionSample(sample: DashboardPredictionSampleWire): PredictionSample {
  return {
    sampleId: sample.sample_id,
    displayReference: sample.display_reference,
    churnProbability: Number(sample.churn_probability),
    contract: sample.Contract,
    tenure: Number(sample.tenure),
    paymentMethod: sample.PaymentMethod,
    monthlyCharges: Number(sample.MonthlyCharges),
    internetService: sample.InternetService,
  };
}

function isDashboardAnalyticsWireResponse(payload: unknown): payload is DashboardAnalyticsWireResponse {
  if (!isRecord(payload)) {
    return false;
  }
  return (
    typeof payload.artifact_version === "string" &&
    isStringRecord(payload.freshness) &&
    isNumberRecord(payload.kpis) &&
    isNumberRecord(payload.risk_distribution) &&
    Array.isArray(payload.prediction_samples) &&
    payload.prediction_samples.every(isDashboardPredictionSampleWire)
  );
}

function isDashboardPredictionSampleWire(sample: unknown): sample is DashboardPredictionSampleWire {
  if (!isRecord(sample)) {
    return false;
  }
  return (
    typeof sample.sample_id === "string" &&
    typeof sample.display_reference === "string" &&
    isStringOrNumber(sample.churn_probability) &&
    typeof sample.Contract === "string" &&
    isStringOrNumber(sample.tenure) &&
    typeof sample.PaymentMethod === "string" &&
    isStringOrNumber(sample.MonthlyCharges) &&
    typeof sample.InternetService === "string"
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isStringRecord(value: unknown): value is Record<string, string> {
  return isRecord(value) && Object.values(value).every((entry) => typeof entry === "string");
}

function isNumberRecord(value: unknown): value is Record<string, number> {
  return isRecord(value) && Object.values(value).every((entry) => typeof entry === "number");
}

function isStringOrNumber(value: unknown): value is string | number {
  return typeof value === "string" || typeof value === "number";
}

function resolveDegradedReason(payload: unknown): string {
  if (typeof payload === "object" && payload !== null && "reason" in payload) {
    const degraded = payload as DegradedDashboardResponse;
    return degraded.reason ?? "Dashboard analytics are unavailable.";
  }
  return "Dashboard analytics are unavailable.";
}
