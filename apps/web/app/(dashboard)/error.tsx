"use client";

export default function DashboardError() {
  return (
    <main className="min-h-screen bg-background px-6 py-8 text-foreground lg:px-10">
      <section className="mx-auto max-w-3xl rounded-2xl border bg-card p-6" role="alert">
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard failed to render</h1>
        <p className="mt-3 text-sm text-muted-foreground">Refresh the page after confirming the API and artifact files are available.</p>
      </section>
    </main>
  );
}
