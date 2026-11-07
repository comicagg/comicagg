const { test, expect, api, expectPost, freezeClock, counters, counterHtml, origin } = require("./fixtures");

const html = counterHtml + `
  <button id="showingUnread" onclick="showAllComics()">Show all</button>
  <button id="showingAll" style="display:none" onclick="showUnreadComics()">Show unread</button>
  <div id="no_unread_comics" style="display:none">Nothing unread</div>
  <div id="noComicsSelected" style="display:none">No subscriptions</div>
  <div id="next_comic_bar" style="display:none"></div>
  <div id="comics">
    ${[1, 2, 3, 4].map((id) => `
      <section id="c${id}" class="comic" style="display:none;height:700px">
        <h2>Comic ${id}</h2>
        <div class="comicextra" style="width:200px">
          <img id="imgu${id}" alt="Unread ${id}">
          <img id="imgl${id}" alt="Latest ${id}">
        </div>
        <span id="working${id}" style="display:none">Working</span>
        <span id="workingerror${id}" style="display:none">Failed</span>
        <span id="ok${id}" style="display:none">Saved</span>
        <span id="newnotice${id}">New</span>
        <div id="reading${id}">
          <button onclick="markread(${id},0)">Mark ${id} read</button>
          <button onclick="markread(${id},1)">Vote ${id} up</button>
          <button onclick="markread(${id},-1)">Vote ${id} down</button>
        </div>
        <button id="reload${id}" style="display:none" onclick="reloadComic(${id})">Reload ${id}</button>
        <button onclick="reportbroken(${id})">Report ${id}</button>
        <button onclick="removecomic(${id})">Remove ${id}</button>
      </section>`).join("")}
  </div>
`;

async function loadReader(page, app, { empty = false, allRead = false, failFirstImage = false } = {}) {
  await page.route(`${origin}/images/**`, (route) => {
    const url = new URL(route.request().url());
    if (failFirstImage && url.pathname === "/images/1.svg" && !url.search) {
      return route.fulfill({ status: 404, body: "" });
    }
    return route.fulfill({
      contentType: "image/svg+xml",
      body: '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="100"><rect width="400" height="100" fill="blue"/></svg>',
    });
  });
  await app.load("read", html);
  await page.evaluate(({ empty, allRead }) => {
    window.titlei18n = "Read";
    window.comics = [];
    window.unreadComics = [];
    if (!empty) {
      for (let id = 1; id <= 4; id++) {
        comics[id] = {
          id, name: `Comic ${id}`, last_url: `/images/${id}.svg`, last_ch: id * 10,
          list: id === 4 ? [] : [{ unreadid: id, chid: id * 10, url: `/images/${id}.svg` }],
          loaded: false, error: false,
        };
        unreadComics[id] = !allRead && id !== 4;
      }
    } else {
      document.getElementById("comics").replaceChildren();
    }
    window.comicCounter = empty ? 0 : 4;
    window.unreadCounter = empty || allRead ? 0 : 3;
    onReadLoad();
  }, { empty, allRead });
}

test("initial reading loads the viewport and one extra comic, then loads more on scroll", async ({ page, app }) => {
  const images = [];
  page.on("request", (request) => {
    if (request.url().startsWith(`${origin}/images/`)) images.push(new URL(request.url()).pathname);
  });
  await loadReader(page, app);
  await expect(page.locator("#imgu1")).toHaveAttribute("src", "/images/1.svg");
  await expect(page.locator("#imgu2")).toHaveAttribute("src", "/images/2.svg");
  expect(images).not.toContain("/images/3.svg");
  await expect(page.locator("#c4")).toBeHidden();
  await page.evaluate(() => window.scrollTo(0, 750));
  await expect(page.locator("#imgu3")).toHaveAttribute("src", "/images/3.svg");
  await expect(page.locator("#imgu1")).toHaveJSProperty("complete", true);
  expect(await page.locator("#imgu1").evaluate((image) => image.style.width)).toBe("100%");
});

test("all/unread controls restore visibility and load a read comic's latest image", async ({ page, app }) => {
  await loadReader(page, app);
  await page.locator("#showingUnread").click();
  await expect(page.locator("#c4")).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, 2200));
  await expect(page.locator("#imgl4")).toHaveAttribute("src", "/images/4.svg");
  await page.locator("#showingAll").click();
  await expect(page.locator("#c4")).toBeHidden();
  await expect(page.locator("#showingUnread")).toBeVisible();
});

test("next-comic navigation scrolls to the extra comic with the fixed-header offset", async ({ page, app }) => {
  await loadReader(page, app);
  await page.evaluate(() => {
    showNextComicBar = true;
    updateViewport(false);
  });
  await expect(page.locator("#next_comic_bar")).toHaveText("Comic 2");
  const top = await page.locator("#c2").evaluate((element) => element.getBoundingClientRect().top + window.scrollY);
  await page.locator("#next_comic_bar a").click();
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(Math.round(top - 40));
});

for (const [label, vote] of [["Mark 1 read", "0"], ["Vote 1 up", "1"], ["Vote 1 down", "-1"]]) {
  test(`${label} posts the vote and changes the reader only after success`, async ({ page, app }) => {
    await loadReader(page, app);
    await freezeClock(page);
    const response = await api(page, "mark-read", { body: { ...counters, unreads: 1 } });
    await page.getByRole("button", { name: label, exact: true }).click();
    expectPost(await response.request, [["id", "1"], ["value", vote]]);
    await expect(page.locator("#working1")).toBeVisible();
    await expect(page.locator("#reading1")).toBeVisible();
    response.release();
    await expect(page.locator("#working1")).toBeHidden();
    await expect(page.locator("#reading1")).toBeHidden();
    await expect(page.locator("#newnotice1")).toBeHidden();
    await expect(page.locator("#ok1")).toBeVisible();
    await expect(page.locator("#menuUnreadCounter")).toHaveText(" (1)");
    expect(await page.evaluate(() => unreadComics[1])).toBe(false);
    await page.clock.runFor(4999);
    await expect(page.locator("#ok1")).toBeVisible();
    await page.clock.runFor(1);
    await expect(page.locator("#ok1")).toBeHidden();
  });
}

for (const [action, endpoint] of [["Mark 1 read", "mark-read"], ["Report 1", "report"], ["Remove 1", "remove"]]) {
  test(`${action} shows a retryable error without removing the comic on HTTP failure`, async ({ page, app }) => {
    await loadReader(page, app);
    const response = await api(page, endpoint, { status: 500 });
    await page.getByRole("button", { name: action, exact: true }).click();
    await response.request;
    await expect(page.locator("#working1")).toBeVisible();
    response.release();
    await expect(page.locator("#workingerror1")).toBeVisible();
    await expect(page.locator("#working1")).toBeHidden();
    await expect(page.locator("#c1")).toBeVisible();
    await expect(page.locator("#reading1")).toBeVisible();
    expect(await page.evaluate(() => unreadComics[1])).toBe(true);
  });
}

for (const id of [1, 4]) {
  test(`reporting comic ${id} sends repeated strip IDs or the latest read strip`, async ({ page, app }) => {
    await loadReader(page, app);
    await page.locator("#showingUnread").click();
    if (id === 1) {
      await page.evaluate(() => comics[1].list.push({ chid: 11 }));
    }
    const response = await api(page, "report");
    await page.getByRole("button", { name: `Report ${id}`, exact: true }).click();
    expectPost(await response.request, id === 1
      ? [["id", "1"], ["id_list[]", "10"], ["id_list[]", "11"]]
      : [["id", "4"], ["id_list[]", "40"]]);
    response.release();
    await expect(page.locator(`#ok${id}`)).toBeVisible();
    await expect(page.locator(`#working${id}`)).toBeHidden();
  });
}

test("image failure exposes reload and retry cache-busts the URL", async ({ page, app }) => {
  await page.route(`${origin}/static/images/error.png`, (route) => route.fulfill({
    contentType: "image/svg+xml", body: '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>',
  }));
  await loadReader(page, app, { failFirstImage: true });
  await expect(page.locator("#reload1")).toBeVisible();
  await expect(page.locator("#imgu1")).toHaveAttribute("alt", "ERROR");
  await expect(page.locator("#imgu1")).toHaveAttribute("src", "/static/images/error.png");
  const requestPromise = page.waitForRequest((request) => /\/images\/1\.svg\?\d+$/.test(request.url()));
  await page.getByRole("button", { name: "Reload 1", exact: true }).click();
  await requestPromise;
  await expect(page.locator("#imgu1")).toHaveAttribute("src", /\/images\/1\.svg\?\d+$/);
  await expect(page.locator("#reload1")).toBeHidden();
});

test("removing the last subscription shows the empty state", async ({ page, app }) => {
  await loadReader(page, app);
  await page.evaluate(() => {
    for (const id of [2, 3, 4]) document.getElementById(`c${id}`).remove();
  });
  const response = await api(page, "remove", { body: { unreads: 0, comics: 0, new_comics: 0, news: 0 } });
  await page.getByRole("button", { name: "Remove 1", exact: true }).click();
  expectPost(await response.request, [["id", "1"]]);
  await expect(page.locator("#c1")).toBeVisible();
  response.release();
  await expect(page.locator("#c1")).toHaveCount(0);
  await expect(page.locator("#noComicsSelected")).toBeVisible();
  expect(await page.evaluate(() => comics[1])).toBeNull();
});

for (const failure of [false, true]) {
  test(`mark-all ${failure ? "failure preserves unread comics" : "success clears unread comics and counters"}`, async ({ page, app }) => {
    await loadReader(page, app);
    const response = await api(page, "mark-all", {
      status: failure ? 500 : 200,
      body: { unreads: 0, comics: 4, new_comics: 0, news: 0 },
    });
    await page.locator("#mark_all_read").click();
    const request = await response.request;
    // Current endpoint intentionally takes no parameters and the legacy client defaults to GET.
    expect(request.method()).toBe("GET");
    expect(request.headers()["x-csrftoken"]).toBeUndefined();
    await expect(page.locator("#mark_all_read_anim")).toBeVisible();
    response.release();
    await expect(page.locator("#mark_all_read_anim")).toBeHidden();
    if (failure) {
      await expect(page.locator("#c1")).toBeVisible();
      expect(await page.evaluate(() => unreadComics[1])).toBe(true);
    } else {
      await expect(page.locator("#no_unread_comics")).toBeVisible();
      await expect(page.locator("#c1")).toBeHidden();
      await expect(page.locator("#mark_all_read_bottom")).toBeHidden();
      await expect(page.locator("#noUnreadCountersTotal")).toHaveText("4");
      expect(await page.evaluate(() => unreadComics.some(Boolean))).toBe(false);
    }
  });
}

for (const [label, options, notice] of [
  ["no subscriptions", { empty: true }, "noComicsSelected"],
  ["no unread comics", { allRead: true }, "no_unread_comics"],
]) {
  test(`reader initialization handles ${label}`, async ({ page, app }) => {
    await loadReader(page, app, options);
    await expect(page.locator(`#${notice}`)).toBeVisible();
    await expect(page.locator("#c1")).toBeHidden();
  });
}
