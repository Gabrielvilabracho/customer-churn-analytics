import { expect, test } from "@playwright/test";

import { PROJECT_METADATA } from "../lib/project-metadata";

test("tooling metadata keeps the E2E runner scoped to the PR0 slice", () => {
  expect(PROJECT_METADATA.deliveryMode).toBe("stacked-to-main");
});
