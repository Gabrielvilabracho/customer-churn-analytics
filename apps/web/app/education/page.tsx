import type { Metadata } from "next";
import { EducationDashboard } from "@/components/features/education/education-dashboard";
import styles from "@/components/features/education/education.module.css";
import { fetchEducationAnalysis } from "@/lib/api/education-client";

export const metadata: Metadata = { title: "Student AI & Burnout | Education Analysis" };
export const dynamic = "force-dynamic";

export default async function EducationPage({ searchParams }: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const scenario = typeof params?.educationScenario === "string" ? params.educationScenario : undefined;
  try {
    const analysis = await fetchEducationAnalysis(fetch, process.env.CHURN_API_BASE_URL ?? "http://127.0.0.1:8000", scenario);
    return <EducationDashboard analysis={analysis} />;
  } catch (error) {
    return <main className={styles.page}><div className={styles.shell}>
      <p className={styles.eyebrow}>Education research / unavailable publication</p>
      <h1>Education analysis unavailable</h1>
      <p role="alert">{error instanceof Error ? error.message : "Unable to load education analysis."}</p>
      <p>Publish a verified education analysis and configure CHURN_ARTIFACT_RUN_ID and CHURN_EDUCATION_ANALYSIS_ID in the API. No demonstration values are substituted.</p>
      <a href="/education">Try again</a>
    </div></main>;
  }
}
