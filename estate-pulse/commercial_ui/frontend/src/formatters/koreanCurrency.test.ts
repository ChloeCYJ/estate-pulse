import { describe, expect, it } from "vitest";

import { formatKoreanCurrency } from "./koreanCurrency";

describe("formatKoreanCurrency", () => {
  it("formats eok values with one decimal place", () => {
    expect(formatKoreanCurrency(1_230_000_000)).toBe("12.3억");
  });

  it("returns dash for nullish values", () => {
    expect(formatKoreanCurrency(null)).toBe("-");
    expect(formatKoreanCurrency(undefined)).toBe("-");
  });
});
