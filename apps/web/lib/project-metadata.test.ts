import { describe, expect, it } from "vitest";

import { PROJECT_METADATA } from "./project-metadata";

describe("PROJECT_METADATA", () => {
  it("identifies the student burnout risk product", () => {
    expect(PROJECT_METADATA.productName).toBe("Student Burnout Risk Command Center");
  });

  it("records the stacked delivery mode", () => {
    expect(PROJECT_METADATA.deliveryMode).toBe("stacked-to-main");
  });
});
