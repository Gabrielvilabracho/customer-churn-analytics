import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { ExecutiveDashboardModel } from "./dashboard-model";

interface DriverSummaryProps {
  model: ExecutiveDashboardModel;
}

export function DriverSummary({ model }: DriverSummaryProps) {
  const leadingCohort = model.contractCohorts[0];
  const topRisk = model.topRiskCustomers[0];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Driver summary</CardTitle>
        <CardDescription>Portfolio narrative derived from the current artifact sample.</CardDescription>
      </CardHeader>
      <CardContent>
        {leadingCohort && topRisk ? (
          <p className="text-sm leading-6 text-muted-foreground">
            {leadingCohort.contract} customers dominate the sampled risk pool, with {leadingCohort.averageChurnProbability} average churn risk. Prioritize outreach for {topRisk.displayReference}, currently labeled {topRisk.riskLabel.toLowerCase()}.
          </p>
        ) : (
          <p className="text-sm text-muted-foreground">No driver narrative is available until prediction samples are generated.</p>
        )}
      </CardContent>
    </Card>
  );
}
