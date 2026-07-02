import { describe, expect, it } from "vitest";

import { PROJECT_METADATA } from "./project-metadata";

describe("PROJECT_METADATA", () => {
  it("identifies the churn analytics product", () => {
    expect(PROJECT_METADATA.productName).toBe("Customer Churn Analytics");
  });

  it("records the stacked delivery mode", () => {
    expect(PROJECT_METADATA.deliveryMode).toBe("stacked-to-main");
  });
});
