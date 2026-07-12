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
      sample("student-001", "Student 001", "0.81", "Engineering", "15", "High", "Restrictive"),
      sample("student-002", "Student 002", "0.43", "Arts", "4", "Low", "Permissive"),
      sample("student-003", "Student 003", "0.16", "Business", "2", "Low", "Permissive"),
    ],
  };
}

function sample(sample_id, display_reference, churn_probability, Major_Category, Weekly_GenAI_Hours, Perceived_AI_Dependency, Institutional_Policy) {
  return { sample_id, display_reference, churn_probability, Major_Category, Weekly_GenAI_Hours, Perceived_AI_Dependency, Institutional_Policy };
}

function sendJson(response, statusCode, payload) {
  response.writeHead(statusCode, { "Content-Type": "application/json" });
  response.end(JSON.stringify(payload));
}
