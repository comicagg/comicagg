const { test, expect, api, expectPost, counters, counterHtml, origin } = require("./fixtures");

test("JSON POSTs preserve encoding, CSRF, pending state and success data", async ({ page, app }) => {
  await app.load();
  const response = await api(page, "request");
  await page.evaluate(() => {
    window.result = "pending";
    startRequest("/api/request", {
      method: "post",
      parameters: { name: "A & B + café", "id_list[]": [11, 12] },
      onSuccess: (data) => { window.result = data; },
      onFailure: () => { window.result = "failed"; },
    });
  });
  expectPost(await response.request, [["name", "A & B + café"], ["id_list[]", "11"], ["id_list[]", "12"]]);
  expect(await page.evaluate(() => window.result)).toBe("pending");
  response.release();
  await expect.poll(() => page.evaluate(() => window.result)).toEqual(counters);
});

for (const failure of [
  { label: "HTTP error", status: 500, body: { error: "failed" } },
  { label: "malformed JSON", status: 200, body: "not JSON" },
]) {
  test(`requests invoke failure rather than success on ${failure.label}`, async ({ page, app }) => {
    await app.load();
    const response = await api(page, "failure", failure);
    await page.evaluate(() => {
      window.result = "pending";
      startRequest("/api/failure", {
        method: "post",
        onSuccess: () => { window.result = "success"; },
        onFailure: () => { window.result = "failure"; },
      });
    });
    await response.request;
    response.release();
    await expect.poll(() => page.evaluate(() => window.result)).toBe("failure");
  });
}

for (const url of ["/api/get", `${origin}/api/get`, "//comicagg.test/api/get"]) {
  test(`GET requests omit CSRF and serialize parameters in the URL: ${url}`, async ({ page, app }) => {
    await app.load();
    await page.route("**/api/get?*", (route) => route.fulfill({ json: counters }));
    const requestPromise = page.waitForRequest("**/api/get?*");
    await page.evaluate((url) => {
      startRequest(url, {
        method: "get",
        parameters: { search: "A & B" },
        onSuccess: () => {},
        onFailure: () => {},
      });
    }, url);
    const request = await requestPromise;
    expect(request.method()).toBe("GET");
    expect(new URL(request.url()).searchParams.get("search")).toBe("A & B");
    expect(request.headers()["x-csrftoken"]).toBeUndefined();
  });
}

test("cross-origin POSTs do not receive the CSRF cookie", async ({ page, app }) => {
  await app.load();
  await page.route("http://external.test/**", (route) => route.fulfill({
    headers: { "Access-Control-Allow-Origin": origin },
    json: counters,
  }));
  const requestPromise = page.waitForRequest("http://external.test/api/request");
  await page.evaluate(() => {
    startRequest("http://external.test/api/request", {
      method: "post",
      parameters: { id: 1 },
      onSuccess: () => {},
      onFailure: () => {},
    });
  });
  expect((await requestPromise).headers()["x-csrftoken"]).toBeUndefined();
});

for (const url of [`${origin}/api/post`, "//comicagg.test/api/post"]) {
  test(`same-origin absolute POSTs receive CSRF: ${url}`, async ({ page, app }) => {
    await app.load();
    const response = await api(page, "post");
    await page.evaluate((url) => {
      window.result = null;
      startRequest(url, {
        method: "post",
        parameters: { id: 1 },
        onSuccess: (data) => { window.result = data; },
        onFailure: () => { window.result = "failure"; },
      });
    }, url);
    expectPost(await response.request, [["id", "1"]]);
    response.release();
    await expect.poll(() => page.evaluate(() => window.result)).toEqual(counters);
  });
}

test("a network failure invokes the failure callback", async ({ page, app }) => {
  await app.load();
  await page.route(`${origin}/api/offline`, (route) => route.abort("connectionfailed"));
  await page.evaluate(() => {
    window.result = "pending";
    startRequest("/api/offline", {
      method: "post",
      onSuccess: () => { window.result = "success"; },
      onFailure: () => { window.result = "failure"; },
    });
  });
  await expect.poll(() => page.evaluate(() => window.result)).toBe("failure");
});

test("an explicit text response is not parsed as JSON", async ({ page, app }) => {
  await app.load();
  const response = await api(page, "text", { body: "plain response", contentType: "text/plain" });
  await page.evaluate(() => {
    window.result = null;
    startRequest("/api/text", {
      method: "get",
      dataType: "text",
      onSuccess: (data) => { window.result = data; },
      onFailure: () => { window.result = "failure"; },
    });
  });
  await response.request;
  response.release();
  await expect.poll(() => page.evaluate(() => window.result)).toBe("plain response");
});

test("read counters update menu text, totals, title and the zero-unread state", async ({ page, app }) => {
  await app.load(null, counterHtml);
  await page.evaluate((counters) => {
    window.titlei18n = "Read";
    updateCounters(counters);
  }, counters);
  await expect(page.locator("#menuUnreadCounter")).toHaveText(" (2)");
  await expect(page.locator("#menuNewComicCounter")).toHaveText(" (1)");
  await expect(page.locator("#menuNewsCounter")).toHaveText(" (1)");
  await expect(page.locator("#unreadCountersUnread")).toHaveText("2");
  await expect(page.locator("#unreadCountersTotal")).toHaveText("3");
  await expect(page).toHaveTitle("Read (2) -  Comic Aggregator");
  await expect(page.locator("#unreadCounters")).toBeVisible();
  await expect(page.locator("#noUnreadCounters")).toBeHidden();

  await page.evaluate(() => updateCounters({ unreads: 0, comics: 3, new_comics: 0, news: 0 }));
  for (const id of ["menuUnreadCounter", "menuNewComicCounter", "menuNewsCounter", "mark_all_read", "unreadCounters"]) {
    await expect(page.locator(`#${id}`)).toBeHidden();
  }
  await expect(page.locator("#noUnreadCounters")).toBeVisible();
  await expect(page.locator("#noUnreadCountersTotal")).toHaveText("3");
  await expect(page).toHaveTitle("Read -  Comic Aggregator");
});

test("counter updates also work outside the reader and without mark-all controls", async ({ page, app }) => {
  await app.load(null, '<span id="menuUnreadCounter"></span><span id="menuNewComicCounter"></span><span id="menuNewsCounter"></span>');
  await page.evaluate(() => updateCounters({ unreads: 0, comics: 1, new_comics: 0, news: 0 }));
  await expect(page.locator("#menuUnreadCounter")).toBeHidden();
  await expect(page).toHaveTitle("Comic Aggregator");
});

test("accepting cookies hides notices, enables login and persists consent", async ({ page, app }) => {
  await app.load(null, `
    <div id="cookie_notice">Cookies</div><div id="cookie_consent_required">Required</div>
    <button id="login_button" type="button">Login</button>
    <button onclick="set_cookie_consent(true)">Accept</button>
  `);
  await page.getByRole("button", { name: "Accept", exact: true }).click();
  await expect(page.locator("#cookie_notice")).toBeHidden();
  await expect(page.locator("#cookie_consent_required")).toBeHidden();
  await expect(page.locator("#login_button")).toHaveAttribute("type", "submit");
  const consent = (await page.context().cookies()).find((cookie) => cookie.name === "cookie_consent");
  expect(consent.value).toBe("true");
  expect(consent.path).toBe("/");
  expect(consent.expires - Date.now() / 1000).toBeGreaterThan(364 * 86400);
  expect(consent.expires - Date.now() / 1000).toBeLessThan(366 * 86400);
});

test("forgetting news posts and clears the news counter", async ({ page, app }) => {
  await app.load(null, counterHtml + '<button onclick="forget_news()">Forget news</button>');
  const response = await api(page, "forget-news", { body: { ...counters, news: 0 } });
  await page.getByRole("button", { name: "Forget news" }).click();
  expectPost(await response.request, []);
  response.release();
  await expect(page.locator("#menuNewsCounter")).toBeHidden();
});

test("login focus and external links retain their targets", async ({ page, app }) => {
  await app.load(null, '<input id="id_username"><button onclick="focusOnLogin()">Focus login</button>');
  await page.getByRole("button", { name: "Focus login" }).click();
  await expect(page.locator("#id_username")).toBeFocused();
  await page.context().route("http://external.test/**", (route) => route.fulfill({ body: "External comic" }));
  const popupPromise = page.waitForEvent("popup");
  expect(await page.evaluate(() => openurl("http://external.test/comic"))).toBe(false);
  const popup = await popupPromise;
  await popup.waitForLoadState();
  expect(popup.url()).toBe("http://external.test/comic");
});

test.fixme("declining cookies completes without throwing when callbacks are omitted", async ({ page, app }) => {
  // Existing startRequest calls undefined onSuccess/onFailure in set_cookie_consent(false).
  await app.load(null, '<div id="cookie_notice">Cookies</div><button onclick="set_cookie_consent(false)">Decline</button>');
  const response = await api(page, "consent");
  await page.getByRole("button", { name: "Decline", exact: true }).click();
  expectPost(await response.request, [["cookie_consent", "false"]]);
  const completed = page.waitForResponse(`${origin}/api/consent`);
  response.release();
  await completed;
  await expect(page.locator("#cookie_notice")).toBeHidden();
  expect((await page.context().cookies()).find((cookie) => cookie.name === "cookie_consent").value).toBe("false");
});
