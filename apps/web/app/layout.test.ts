import { describe, expect, it } from "vitest";

import { metadata } from "./layout";

describe("RootLayout metadata", () => {
  it("exports the education-domain description for user-facing SEO and link previews", () => {
    expect(metadata.description).toBe(
      "AI-powered student burnout risk prediction and retention intelligence.",
    );
  });
});
