"use client";

import { useEffect, useState } from "react";

import { CohortChart } from "@/components/features/churn/cohort-chart";
import { buildExecutiveDashboardModel } from "@/components/features/churn/dashboard-model";
import { DriverSummary } from "@/components/features/churn/driver-summary";
import { KpiCards } from "@/components/features/churn/kpi-cards";
import { RiskTable } from "@/components/features/churn/risk-table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DashboardAnalyticsError, fetchDashboardAnalytics } from "@/lib/api/client";
import type { DashboardAnalytics } from "@/lib/api/types";

interface DashboardClientProps {
  initialAnalytics?: DashboardAnalytics;
  initialError?: string;
}

export function DashboardClient({ initialAnalytics, initialError }: DashboardClientProps) {
  const [analytics, setAnalytics] = useState<DashboardAnalytics | undefined>(initialAnalytics);
  const [errorMessage, setErrorMessage] = useState<string | undefined>(initialError);

  useEffect(() => {
    if (initialAnalytics || initialError) {
      return;
    }

    let isActive = true;

    fetchDashboardAnalytics()
      .then((nextAnalytics) => {
        if (!isActive) {
          return;
        }
        setAnalytics(nextAnalytics);
        setErrorMessage(undefined);
      })
      .catch((error: unknown) => {
        if (!isActive) {
          return;
        }
        setErrorMessage(resolveDashboardErrorMessage(error));
      });

    return () => {
      isActive = false;
    };
  }, [initialAnalytics, initialError]);

  if (analytics) {
    return <DashboardContent analytics={analytics} />;
  }

  if (errorMessage) {
    return <DashboardErrorState message={errorMessage} />;
  }

  return (
    <main className="min-h-screen bg-background px-6 py-8 text-foreground lg:px-10">
      <p className="text-sm text-muted-foreground" aria-live="polite">Loading dashboard analytics…</p>
    </main>
  );
}

function DashboardContent({ analytics }: { analytics: DashboardAnalytics }) {
  const model = buildExecutiveDashboardModel(analytics);

  return (
    <main className="min-h-screen bg-background px-6 py-8 text-foreground lg:px-10">
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        <header className="flex flex-col gap-3">
          <p className="text-sm font-medium uppercase tracking-wide text-muted-foreground">Student retention intelligence</p>
          <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
            <div className="flex flex-col gap-3">
              <h1 className="max-w-3xl text-4xl font-semibold tracking-tight">Student burnout-risk command center</h1>
              <p className="max-w-2xl text-base leading-7 text-muted-foreground">
                API-backed model outputs translated into retention priorities, cohort exposure, and student-level risk.
              </p>
            </div>
            <p className="text-sm text-muted-foreground">Artifact {model.artifactVersion} · Freshness {model.freshnessLabel}</p>
          </div>
        </header>

        <KpiCards cards={model.kpiCards} />

        <section className="grid gap-6 xl:grid-cols-[1fr_1.15fr]">
          <CohortChart cohorts={model.majorCategoryCohorts} />
          <DriverSummary model={model} />
        </section>

        <RiskTable customers={model.topRiskCustomers} />
      </div>
    </main>
  );
}

function DashboardErrorState({ message }: { message: string }) {
  return (
    <main className="min-h-screen bg-background px-6 py-8 text-foreground lg:px-10">
      <div className="mx-auto max-w-3xl">
        <Card>
          <CardHeader>
            <CardTitle>Analytics artifacts are unavailable</CardTitle>
            <CardDescription>{message}</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">Run the ML training pipeline and refresh the API artifacts.</p>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}

function resolveDashboardErrorMessage(error: unknown): string {
  if (error instanceof DashboardAnalyticsError) {
    return error.message;
  }
  return "Dashboard analytics are unavailable.";
}
