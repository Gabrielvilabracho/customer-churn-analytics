import { expect, test } from "@playwright/test";

test("tooling smoke test loads the dashboard route in a browser", async ({ page }) => {
  await page.goto("/");

  await expect(page).toHaveTitle("Student Burnout Risk Command Center");
  await expect(page.getByRole("heading", { name: "Student burnout-risk command center" })).toBeVisible();
});
