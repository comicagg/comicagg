const path = require("node:path");
const { test: base, expect } = require("@playwright/test");

const origin = "http://comicagg.test";
const staticRoot = path.resolve(__dirname, "../../src/static_files");
const counters = { unreads: 2, comics: 3, new_comics: 1, news: 1 };
const counterHtml = `
  <span id="menuUnreadCounter"></span>
  <span id="menuNewComicCounter"></span>
  <span id="menuNewsCounter"></span>
  <div id="unreadCounters">
    <span id="unreadCountersUnread"></span><span id="unreadCountersTotal"></span>
  </div>
  <div id="noUnreadCounters" style="display:none">
    <span id="noUnreadCountersTotal"></span>
  </div>
  <button id="mark_all_read" onclick="mark_all_read()">Mark all read</button>
  <span id="mark_all_read_anim" style="display:none">Working</span>
  <button id="mark_all_read_bottom" onclick="mark_all_read()">Mark all read</button>
`;

const test = base.extend({
  app: async ({ page }, use) => {
    const errors = [];
    const unexpectedRequests = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.context().route("**/*", (route) => {
      unexpectedRequests.push(`${route.request().method()} ${route.request().url()}`);
      return route.abort();
    });
    await use({
      async load(script, html = "") {
        await page.route(`${origin}/fixture`, (route) =>
          route.fulfill({
            contentType: "text/html",
            body: `<!doctype html><html><head><title>Comic Aggregator</title>
              <style>body { margin: 0; } button { min-height: 24px; }</style>
              </head><body>${html}</body></html>`,
          }),
        );
        await page.goto(`${origin}/fixture`);
        await page.context().addCookies([
          { name: "csrftoken", value: "test%2Dtoken", url: origin },
        ]);
        await page.evaluate(() => {
          Object.assign(window, {
            titlebase: " Comic Aggregator",
            static_url: "/static/",
            unreadCounter: 2,
            comicCounter: 3,
            newComicCounter: 1,
            newsCounter: 1,
            url_mark_as_read: "/api/mark-read",
            url_mark_all_read: "/api/mark-all",
            url_remove: "/api/remove",
            url_report: "/api/report",
            url_save_selection: "/api/save",
            url_remove_list: "/api/remove-list",
            url_forget_new_blogs: "/api/forget-news",
          });
        });
        await page.addScriptTag({ path: path.join(staticRoot, "base/js/all.js") });
        if (script) {
          await page.addScriptTag({ path: path.join(staticRoot, `base/js/${script}.js`) });
        }
      },
    });
    expect(errors, "Unexpected uncaught browser errors").toEqual([]);
    expect(unexpectedRequests, "Unexpected HTTP requests").toEqual([]);
  },
});

async function api(page, endpoint, { status = 200, body = counters, contentType = "application/json" } = {}) {
  let release;
  const ready = new Promise((resolve) => {
    release = resolve;
  });
  const request = page.waitForRequest(`${origin}/api/${endpoint}`);
  await page.route(`${origin}/api/${endpoint}`, async (route) => {
    await ready;
    await route.fulfill({
      status,
      contentType,
      body: typeof body === "string" ? body : JSON.stringify(body),
    });
  });
  return { request, release };
}

function expectPost(request, parameters) {
  expect(request.method()).toBe("POST");
  if (parameters.length) {
    expect(request.headers()["content-type"]).toContain("application/x-www-form-urlencoded");
  }
  expect(request.headers()["x-csrftoken"]).toBe("test-token");
  const body = new URLSearchParams(request.postData() || "");
  expect([...body.entries()]).toEqual(parameters);
}

async function freezeClock(page) {
  const time = new Date("2026-01-01T00:00:00Z");
  await page.clock.install({ time });
  await page.clock.pauseAt(time);
}

module.exports = { test, expect, api, expectPost, freezeClock, counters, counterHtml, origin };
