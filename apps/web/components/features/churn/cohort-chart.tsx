import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { MajorCategoryCohortModel } from "./dashboard-model";

interface CohortChartProps {
  cohorts: MajorCategoryCohortModel[];
}

export function CohortChart({ cohorts }: CohortChartProps) {
  if (cohorts.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Major category cohorts</CardTitle>
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
        <CardTitle>Major category cohorts</CardTitle>
        <CardDescription>Average burnout risk grouped by student major category.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-4" role="list" aria-label="Major category cohort risk summary">
          {cohorts.map((cohort) => (
            <div key={cohort.majorCategory} className="flex flex-col gap-2" role="listitem">
              <div className="flex items-center justify-between gap-4 text-sm">
                <span className="font-medium">{cohort.majorCategory}</span>
                <span className="text-muted-foreground">
                  {cohort.customers} students · {cohort.averageChurnProbability} risk
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
