import { expect, test } from "@playwright/test";

test("education analysis supports variables, cohorts and individual explanations", async ({ page }) => {
  await page.goto("/education");
  await expect(page.getByRole("heading", { name: "Burnout & AI study" })).toBeVisible();
  await expect(page.getByText("synthetic-analysis", { exact: true })).toBeVisible();
  await page.getByLabel("Variable to inspect").selectOption("Major_Category");
  await expect(page.getByRole("rowheader", { name: "Engineering", exact: true })).toBeVisible();
  await expect(page.getByRole("cell", { name: "negative", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Cohorts", exact: true }).click();
  await expect(page.getByRole("columnheader", { name: "Observed high burnout" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "60.0%", exact: true }).first()).toBeVisible();
  await page.getByLabel("Cohort variable").selectOption("Weekly_GenAI_Hours");
  await expect(page.getByText("Suppressed", { exact: true }).first()).toBeVisible();
  const suppressedRow = page.getByRole("row").filter({
    has: page.getByRole("rowheader", { name: "(10, 20]", exact: true }),
  });
  await expect(suppressedRow.getByRole("cell")).toHaveText([
    "5", "Suppressed", "Suppressed", "Suppressed", "Suppressed", "Suppressed",
  ]);
  await page.getByRole("button", { name: "Explanations", exact: true }).click();
  await page.getByLabel("Anonymized held-out sample").selectOption("sample-0002");
  await expect(page.getByRole("img", { name: "SHAP waterfall for sample-0002" })).toBeVisible();
  await expect(page.getByRole("img", { name: "SHAP waterfall for sample-0002" }).locator("g text"))
    .toHaveText(["Weekly GenAI Hours", "-0.200", "Major Category", "-0.100"]);
  await expect(page.getByText("42.6%", { exact: true })).toBeVisible();
  await expect(page.getByText("Qualified human review is required.", { exact: false })).toBeVisible();
});

test("education analysis has honest empty and degraded states", async ({ page }) => {
  await page.goto("/education?educationScenario=empty");
  await expect(page.getByText("No variable analysis is available.")).toBeVisible();
  await page.getByRole("button", { name: "Cohorts", exact: true }).click();
  await expect(page.getByText("No cohort comparisons are available.")).toBeVisible();
  await page.getByRole("button", { name: "Explanations", exact: true }).click();
  await expect(page.getByText("No held-out explanations are available.")).toBeVisible();
  await page.goto("/education?educationScenario=degraded");
  await expect(page.getByRole("heading", { name: "Education analysis unavailable" })).toBeVisible();
  await expect(page.getByText("Education analysis is not published.")).toBeVisible();
  await expect(page.getByRole("link", { name: "Try again" })).toBeVisible();
});

test("undefined cohort metrics are not labeled as policy-suppressed", async ({ page }) => {
  await page.goto("/education?educationScenario=undefined");
  await page.getByRole("button", { name: "Cohorts", exact: true }).click();
  await expect(page.getByRole("cell", { name: "Undefined", exact: true })).toHaveCount(4);
  await expect(page.getByRole("cell", { name: "Suppressed", exact: true })).toHaveCount(0);
});
