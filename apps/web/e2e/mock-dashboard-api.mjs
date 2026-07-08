import { createServer } from "node:http";

const server = createServer(async (request, response) => {
  if (!request.url) {
    sendJson(response, 404, { reason: "Not found" });
    return;
  }

  const url = new URL(request.url, "http://127.0.0.1:3100");

  if (url.pathname === "/health") {
    sendJson(response, 200, { status: "ready" });
    return;
  }

  if (url.pathname === "/analytics/dashboard") {
    const scenario = url.searchParams.get("scenario") ?? "happy";

    if (scenario === "degraded") {
      sendJson(response, 503, { status: "degraded", reason: "metrics artifact is missing" });
      return;
    }

    const payload = dashboardPayload();
    if (scenario === "empty") {
      sendJson(response, 200, { ...payload, risk_distribution: {}, prediction_samples: [] });
      return;
    }

    sendJson(response, 200, payload);
    return;
  }

  sendJson(response, 404, { reason: "Not found" });
});

server.listen(3100, "127.0.0.1");

function dashboardPayload() {
  return {
    artifact_version: "run-2026-07-02",
    freshness: { metrics_created_at_utc: "2026-07-02T00:00:00Z" },
    kpis: { pr_auc: 0.82, recall: 0.74 },
    risk_distribution: { high: 2, low: 1 },
    threshold: 0.5,
    prediction_samples: [
      sample("sample-001", "Sample 001", "0.81", "Month-to-month", "Electronic check", "Fiber optic"),
      sample("sample-002", "Sample 002", "0.43", "Month-to-month", "Mailed check", "DSL"),
      sample("sample-003", "Sample 003", "0.16", "Two year", "Credit card", "DSL"),
    ],
  };
}

function sample(sample_id, display_reference, churn_probability, Contract, PaymentMethod, InternetService) {
  return { sample_id, display_reference, churn_probability, Contract, PaymentMethod, InternetService, MonthlyCharges: "50", tenure: "12" };
}

function sendJson(response, statusCode, payload) {
  response.writeHead(statusCode, { "Content-Type": "application/json" });
  response.end(JSON.stringify(payload));
}
