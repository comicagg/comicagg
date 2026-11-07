const { readFileSync } = require("node:fs");
const path = require("node:path");
const { test, expect, api, freezeClock } = require("./fixtures");

function template(relativePath) {
  return readFileSync(path.resolve(__dirname, "../../src", relativePath), "utf8");
}

test("the blog sidebar's template hook scrolls below the fixed header", async ({ page, app }) => {
  const source = template("blog/templates/blog/side.html");
  const match = source.match(/onclick="([^"]+)"/);
  expect(match, "Blog navigation event hook").not.toBeNull();
  const onclick = match[1].replace("{{ item.id }}", "1");
  await app.load(null, `
    <a onclick="${onclick}">Recent post</a>
    <article id="p1" style="position:absolute;top:900px;height:700px">Post</article>
  `);
  await page.getByText("Recent post", { exact: true }).click();
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(860);
});

test("the request template's confirmation hides after ten seconds", async ({ page, app }) => {
  const source = template("comics/templates/comics/request_index.html");
  const match = source.match(/<script type="text\/javascript">([\s\S]*?)<\/script>/);
  expect(match, "Request confirmation timer").not.toBeNull();
  await app.load(null, '<div id="thanks">Request received</div>');
  await freezeClock(page);
  await page.addScriptTag({ content: match[1] });
  await page.clock.runFor(9999);
  await expect(page.locator("#thanks")).toBeVisible();
  await page.clock.runFor(1);
  await expect(page.locator("#thanks")).toBeHidden();
});

for (const [id, value] of [
  ["accept_cookies", "1"],
  ["reject_cookies", "0"],
]) {
  test(`the cookie notice submits ${value === "1" ? "acceptance" : "rejection"} to the server`, async ({ page, app }) => {
    const source = template("about/templates/about/cookie_notice.html");
    const markup = source
      .replace("{% load i18n %}", "")
      .replaceAll("{% url 'about:consent' %}", "/api/consent")
      .replaceAll("{% csrf_token %}", '<input type="hidden" name="csrfmiddlewaretoken" value="test-token">');
    await app.load(null, markup);
    const response = await api(page, "consent");
    const submission = page.locator(`#${id}`).click();
    const request = await response.request;
    expect(request.method()).toBe("POST");
    const parameters = new URLSearchParams(request.postData() || "");
    expect(parameters.get("cookie_consent")).toBe(value);
    expect(parameters.get("csrfmiddlewaretoken")).toBe("test-token");
    response.release();
    await submission;
  });
}
