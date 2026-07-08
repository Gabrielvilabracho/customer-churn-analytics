import { DashboardAnalyticsError, fetchDashboardAnalytics } from "@/lib/api/client";
import { DashboardClient } from "./dashboard-client";

interface DashboardPageProps {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}

export default async function DashboardPage({ searchParams }: DashboardPageProps) {
  const params = await searchParams;
  const dashboardScenario = resolveDashboardScenario(params?.dashboardScenario);

  try {
    const analytics = await fetchDashboardAnalytics(fetch, process.env.CHURN_API_BASE_URL ?? "http://localhost:8000", { dashboardScenario });
    return <DashboardClient initialAnalytics={analytics} />;
  } catch (error) {
    return <DashboardClient initialError={resolveDashboardErrorMessage(error)} />;
  }
}

function resolveDashboardScenario(value: string | string[] | undefined): string | undefined {
  if (Array.isArray(value)) {
    return value[0];
  }
  return value;
}

function resolveDashboardErrorMessage(error: unknown): string {
  if (error instanceof DashboardAnalyticsError) {
    return error.message;
  }
  return "Dashboard analytics are unavailable.";
}
