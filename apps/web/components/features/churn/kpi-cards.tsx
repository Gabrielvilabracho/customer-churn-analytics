import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { KpiCardModel } from "./dashboard-model";

interface KpiCardsProps {
  cards: KpiCardModel[];
}

export function KpiCards({ cards }: KpiCardsProps) {
  return (
    <section aria-label="Student burnout-risk KPIs" className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => (
        <Card key={card.label}>
          <CardHeader>
            <CardDescription>{card.label}</CardDescription>
            <CardTitle>{card.value}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">{card.detail}</p>
          </CardContent>
        </Card>
      ))}
    </section>
  );
}
