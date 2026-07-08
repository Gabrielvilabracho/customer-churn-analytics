export default function DashboardLoading() {
  return (
    <main className="min-h-screen bg-background px-6 py-8 text-foreground lg:px-10" aria-busy="true" aria-live="polite">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <p className="text-sm font-medium uppercase tracking-wide text-muted-foreground">Loading churn analytics</p>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="h-32 rounded-2xl border bg-card" />
          ))}
        </div>
      </div>
    </main>
  );
}
