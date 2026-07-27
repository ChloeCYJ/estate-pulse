import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(frontendRoot, "..", "..");
const outputDir = path.join(repoRoot, "artifacts", "commercial-ui", "search-home");
const buildCssPath = path.join(frontendRoot, "build", "commercial-ui.css");
const baseUrl = process.env.SEARCH_HOME_BASE_URL ?? "http://localhost:8508";

await mkdir(outputDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const cssResponses = [];
const consoleErrors = [];

page.on("response", async (response) => {
  const url = response.url();
  if (!url.includes("/_stcore/bidi-components/commercial_ui.commercial_ui/") || !url.endsWith(".css")) {
    return;
  }
  const body = await response.body();
  cssResponses.push({
    url,
    status: response.status(),
    size: body.byteLength
  });
});

page.on("console", (message) => {
  if (message.type() === "error") {
    consoleErrors.push(message.text());
  }
});

await page.goto(baseUrl, { waitUntil: "networkidle" });
await waitForCommercialRoot(page);

const evidence = {
  timestamp: new Date().toISOString(),
  baseUrl,
  desktop: await captureViewportState(page, {
    width: 1440,
    height: 1000,
    idleShot: path.join(outputDir, "desktop-idle.png"),
    recentShot: path.join(outputDir, "desktop-recent.png")
  }),
  mobile: null,
  cssResponses,
  cssSelectors: await inspectCssSelectors(buildCssPath),
  consoleErrors
};

const mobilePage = await browser.newPage({ viewport: { width: 390, height: 844 } });
mobilePage.on("console", (message) => {
  if (message.type() === "error") {
    consoleErrors.push(message.text());
  }
});
await mobilePage.goto(baseUrl, { waitUntil: "networkidle" });
await waitForCommercialRoot(mobilePage);
evidence.mobile = await captureViewportState(mobilePage, {
  width: 390,
  height: 844,
  idleShot: path.join(outputDir, "mobile-idle.png"),
  recentShot: path.join(outputDir, "mobile-recent.png")
});

await writeFile(
  path.join(outputDir, "after-fix-evidence.json"),
  `${JSON.stringify(evidence, null, 2)}\n`,
  "utf8"
);

await browser.close();

async function captureViewportState(pageInstance, screenshots) {
  await pageInstance.setViewportSize({ width: screenshots.width, height: screenshots.height });
  await pageInstance.evaluate(() => window.scrollTo(0, 0));
  await pageInstance.screenshot({ path: screenshots.idleShot, fullPage: false });
  const computed = await pageInstance.evaluate(() => {
    const scope =
      Array.from(document.querySelectorAll("*"))
        .map((element) => element.shadowRoot)
        .find((shadowRoot) => shadowRoot?.querySelector(".ep-shell")) ?? document;

    const root = scope.querySelector(".ep-shell");
    const layout = scope.querySelector(".ep-layout");
    const input = scope.querySelector(".ep-searchbar__input");
    const button = scope.querySelector(".ep-button--primary");
    const card = scope.querySelector(".ep-recent-card");
    const topNavItem = scope.querySelector(".ep-topnav__item");
    const activeTopNavItem = scope.querySelector(".ep-topnav__item.is-active");
    const searchControls = scope.querySelector(".ep-searchbar__controls");
    const emptyIdlePanel = Array.from(scope.querySelectorAll("section, div")).find((element) =>
      element.textContent?.includes("검색을 시작해 주세요")
    );
    const headlineText = scope.querySelector("h1")?.textContent?.trim() ?? "";
    const headingMatches = Array.from(scope.querySelectorAll("h1, h2, h3")).filter(
      (element) => element.textContent?.trim() === headlineText
    );

    return {
      rootClassName: root?.className ?? null,
      rootBackground: root ? getComputedStyle(root).backgroundColor : null,
      layoutMaxWidth: layout ? getComputedStyle(layout).maxWidth : null,
      layoutDisplay: layout ? getComputedStyle(layout).display : null,
      layoutPaddingInline: layout ? getComputedStyle(layout).paddingInline : null,
      searchControlsLayout: searchControls ? getComputedStyle(searchControls).gridTemplateColumns : null,
      input: input
        ? {
            border: getComputedStyle(input).border,
            height: getComputedStyle(input).height,
            padding: getComputedStyle(input).padding
          }
        : null,
      primaryButton: button
        ? {
            backgroundColor: getComputedStyle(button).backgroundColor,
            borderRadius: getComputedStyle(button).borderRadius,
            height: getComputedStyle(button).height
          }
        : null,
      recentCard: card
        ? {
          border: getComputedStyle(card).border,
          padding: getComputedStyle(card).padding,
          borderRadius: getComputedStyle(card).borderRadius
        }
        : null,
      topNavItem: topNavItem
        ? {
            backgroundColor: getComputedStyle(topNavItem).backgroundColor,
            border: getComputedStyle(topNavItem).border
          }
        : null,
      activeTopNavItem: activeTopNavItem
        ? {
            color: getComputedStyle(activeTopNavItem).color
          }
        : null,
      duplicateHeadlineCount: headingMatches.length,
      hasIdleSearchPanel: Boolean(emptyIdlePanel),
      sidebarDomPresent:
        document.querySelector('[data-testid="stSidebar"]') !== null ||
        document.querySelector("section[data-testid='stSidebar']") !== null,
      horizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
      recentGridColumns:
        scope.querySelector(".ep-recent-grid") !== null
          ? getComputedStyle(scope.querySelector(".ep-recent-grid")).gridTemplateColumns
          : null
    };
  });

  const recentTitle = pageInstance.locator("#recent-analyses-title");
  if ((await recentTitle.count()) > 0) {
    await recentTitle.scrollIntoViewIfNeeded();
    await pageInstance.waitForTimeout(150);
  }
  await pageInstance.screenshot({ path: screenshots.recentShot, fullPage: false });

  return computed;
}

async function waitForCommercialRoot(pageInstance) {
  await pageInstance.waitForSelector("text=서울 아파트를 숫자로 판단하세요");
  await pageInstance.waitForFunction(
    () =>
      Array.from(document.querySelectorAll("*")).some((element) =>
        element.shadowRoot?.querySelector(".ep-shell")
      ),
    { timeout: 10000 }
  );
  await pageInstance.waitForTimeout(300);
}

async function inspectCssSelectors(cssPath) {
  const cssText = await readFile(cssPath, "utf8");
  const selectors = [
    ".ep-shell",
    ".ep-layout",
    ".ep-searchbar__input",
    ".ep-button--primary",
    ".ep-recent-card",
    ".ep-recent-grid"
  ];

  return {
    path: cssPath,
    size: cssText.length,
    selectors: Object.fromEntries(selectors.map((selector) => [selector, cssText.includes(selector)]))
  };
}
