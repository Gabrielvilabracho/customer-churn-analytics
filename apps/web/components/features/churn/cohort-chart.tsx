import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { ContractCohortModel } from "./dashboard-model";

interface CohortChartProps {
  cohorts: ContractCohortModel[];
}

export function CohortChart({ cohorts }: CohortChartProps) {
  if (cohorts.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Contract cohorts</CardTitle>
          <CardDescription>No prediction samples are available yet.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Run the training pipeline to publish cohort-ready prediction samples.</p>
        </CardContent>
      </Card>
    );
  }

  const maxCustomers = Math.max(...cohorts.map((cohort) => cohort.customers));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Contract cohorts</CardTitle>
        <CardDescription>Average churn risk grouped by customer contract.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-4" role="list" aria-label="Contract cohort risk summary">
          {cohorts.map((cohort) => (
            <div key={cohort.contract} className="flex flex-col gap-2" role="listitem">
              <div className="flex items-center justify-between gap-4 text-sm">
                <span className="font-medium">{cohort.contract}</span>
                <span className="text-muted-foreground">
                  {cohort.customers} customers · {cohort.averageChurnProbability} risk
                </span>
              </div>
              <div className="h-2 rounded-full bg-secondary" aria-hidden="true">
                <div className="h-2 rounded-full bg-primary" style={{ width: `${(cohort.customers / maxCustomers) * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
