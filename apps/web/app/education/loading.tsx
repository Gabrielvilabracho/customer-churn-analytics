import styles from "@/components/features/education/education.module.css";

export default function LoadingEducation() {
  return <main className={styles.page} aria-busy="true"><div className={styles.shell}>
    <p role="status">Loading verified education analysis…</p>
  </div></main>;
}
