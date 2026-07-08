import { expect, test } from "@playwright/test";

test("tooling smoke test loads the dashboard route in a browser", async ({ page }) => {
  await page.goto("/");

  await expect(page).toHaveTitle("Customer Churn Analytics");
  await expect(page.getByRole("heading", { name: "Executive churn command center" })).toBeVisible();
});
