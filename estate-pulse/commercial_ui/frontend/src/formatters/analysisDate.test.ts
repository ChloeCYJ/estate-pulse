import { describe, expect, it } from "vitest";

import { formatAnalysisDateLabel } from "./analysisDate";

describe("formatAnalysisDateLabel", () => {
  it("formats an ISO-like timestamp as a compact Korean date", () => {
    expect(formatAnalysisDateLabel("2026-07-13 12:28")).toBe("2026.07.13");
  });

  it("returns the original string when parsing is not possible", () => {
    expect(formatAnalysisDateLabel("최근")).toBe("최근");
  });

  it("returns a dash when the source value is empty", () => {
    expect(formatAnalysisDateLabel("   ")).toBe("-");
  });
});
