// @vitest-environment node

import { describe, expect, it } from "vitest";

import viteConfig from "./vite.config";

describe("vite config", () => {
  it("defines process.env.NODE_ENV for browser-safe production bundles", () => {
    const resolvedConfig = viteConfig({
      command: "build",
      isPreview: false,
      isSsrBuild: false,
      mode: "production"
    });

    expect(resolvedConfig.define).toMatchObject({
      "process.env.NODE_ENV": "\"production\""
    });
    expect(resolvedConfig.build?.emptyOutDir).toBe(false);
  });
});
