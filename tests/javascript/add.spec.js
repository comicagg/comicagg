const { test, expect, freezeClock } = require("./fixtures");

const html = `
  <input id="search_box" onkeyup="filter(this.value)">
  <button onclick="filter_all()">All</button><button onclick="filter_new()">New</button>
  <button onclick="filter_running()">Running</button><button onclick="filter_added()">Added</button>
  <div id="comic_list" style="position:absolute;top:120px">
    <div id="alpha" class="new added">Alpha Comic</div>
    <div id="beta" class="broken">Beta Comic</div>
    <div id="gamma" class="ended added">Gamma Comic</div>
    <div id="delta">Delta Comic</div>
  </div>
  <div id="comic_info" style="position:absolute;top:200px;height:300px"></div>
  <div id="last_image" style="position:absolute;top:250px;height:20px">Image</div>
  <div id="last_image_broken" style="display:none">Broken</div>
`;

test.beforeEach(async ({ app }) => app.load("add", html));

test("search filters names and restores all items when cleared", async ({ page }) => {
  await page.locator("#search_box").fill("alpha");
  await page.locator("#search_box").press("End");
  await expect(page.locator("#alpha")).toBeVisible();
  for (const id of ["beta", "gamma", "delta"]) {
    await expect(page.locator(`#${id}`)).toBeHidden();
  }
  await page.getByRole("button", { name: "All", exact: true }).click();
  await expect(page.locator("#search_box")).toHaveValue("");
  for (const id of ["alpha", "beta", "gamma", "delta"]) {
    await expect(page.locator(`#${id}`)).toBeVisible();
  }
});

for (const [label, keyword, visible] of [
  ["New", "@new", ["alpha"]],
  ["Added", "@added", ["alpha", "gamma"]],
  ["Running", "@running", ["alpha", "delta"]],
]) {
  test(`${label} quick filter preserves the status rules`, async ({ page }) => {
    await page.getByRole("button", { name: label, exact: true }).click();
    await expect(page.locator("#search_box")).toHaveValue(keyword);
    for (const id of ["alpha", "beta", "gamma", "delta"]) {
      if (visible.includes(id)) await expect(page.locator(`#${id}`)).toBeVisible();
      else await expect(page.locator(`#${id}`)).toBeHidden();
    }
  });
}

test("search debounces for 100ms and applies only the most recent input", async ({ page }) => {
  await freezeClock(page);
  await page.locator("#search_box").fill("alpha");
  await page.locator("#search_box").press("End");
  await page.clock.runFor(50);
  await page.locator("#search_box").fill("beta");
  await page.locator("#search_box").press("End");
  await page.clock.runFor(99);
  await expect(page.locator("#alpha")).toBeVisible();
  await page.clock.runFor(1);
  await expect(page.locator("#alpha")).toBeHidden();
  await expect(page.locator("#beta")).toBeVisible();
});

test("image failures and subsequent loads switch the notices and calculate available height", async ({ page }) => {
  await page.evaluate(() => last_image_onerror());
  await expect(page.locator("#last_image")).toBeHidden();
  await expect(page.locator("#last_image_broken")).toBeVisible();
  await page.evaluate(() => last_image_onload());
  await expect(page.locator("#last_image")).toBeVisible();
  await expect(page.locator("#last_image_broken")).toBeHidden();
  expect(await page.evaluate(() => document.documentElement.style.getPropertyValue("--comic-image-height"))).toBe("250px");
});

test("resize recalculates list height using viewport and list offset", async ({ page }) => {
  await page.setViewportSize({ width: 900, height: 700 });
  await expect.poll(() => page.evaluate(() =>
    document.documentElement.style.getPropertyValue("--comic-list-height"),
  )).toBe("580px");
  expect(await page.evaluate(() => document.documentElement.style.getPropertyValue("--scrollbar-width"))).toBe("0px");
});

test.fixme("search accepts quotes as ordinary text", async ({ page }) => {
  // Existing filter interpolates input into a string-based setTimeout and raises SyntaxError.
  await page.locator("#search_box").fill('"alpha"');
  await page.locator("#search_box").press("End");
  for (const id of ["alpha", "beta", "gamma", "delta"]) {
    await expect(page.locator(`#${id}`)).toBeHidden();
  }
});
