import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import DashboardLoading from "./loading";

describe("DashboardLoading", () => {
  it("renders a semantic loading state with the student burnout risk copy contract", () => {
    const html = renderToStaticMarkup(DashboardLoading());

    // Semantic loading attributes — announces loading to assistive technology
    expect(html).toContain('aria-busy="true"');
    expect(html).toContain('aria-live="polite"');

    // Visible loading copy — user-observable contract
    expect(html).toContain("Loading student burnout analytics");

    // Loading state renders skeleton card placeholders (not just empty text)
    expect(html).toContain("bg-card");
  });
});
