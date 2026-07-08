import { expect, test } from "@playwright/test";

test("dashboard happy path surfaces enriched cohort analytics in the browser", async ({ page }) => {
  await page.goto("/?dashboardScenario=happy");

  await expect(page.getByRole("heading", { name: "Executive churn command center" })).toBeVisible();
  await expect(page.getByText("Artifact run-2026-07-02")).toBeVisible();
  await expect(page.getByRole("cell", { name: "Sample 001" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "Sample 003" })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Risk" })).toHaveAttribute("aria-sort", "descending");

  await page.getByRole("button", { name: "Sort by customer descending" }).click();

  await expect(page.getByRole("columnheader", { name: "Customer" })).toHaveAttribute("aria-sort", "descending");
  const customerCells = page.getByRole("cell").filter({ hasText: /^Sample/ });
  await expect(customerCells).toHaveText(["Sample 003", "Sample 002", "Sample 001"]);
});

test("dashboard empty predictions state explains the next modeling step", async ({ page }) => {
  await page.goto("/?dashboardScenario=empty");

  await expect(page.getByText("No prediction samples are available yet.")).toBeVisible();
  await expect(page.getByText("Run the training pipeline to publish prediction rows")).toBeVisible();
  await expect(page.getByText("No customer risk rows are available.")).toBeVisible();
});

test("dashboard degraded path preserves artifact failure reason in the browser", async ({ page }) => {
  await page.goto("/?dashboardScenario=degraded");

  await expect(page.getByRole("heading", { name: "Analytics artifacts are unavailable" })).toBeVisible();
  await expect(page.getByText("metrics artifact is missing")).toBeVisible();
  await expect(page.getByText("Run the ML training pipeline and refresh the API artifacts.")).toBeVisible();
});
