const { test, expect, api, expectPost, freezeClock, counterHtml } = require("./fixtures");

const html = counterHtml + `
  <div id="user_comics"></div><div id="trash"></div>
  <span id="saving_text" style="display:none">Saving</span>
  <span id="saved" style="display:none">Saved</span>
  <span id="save_error" style="display:none">Failed</span>
  <button onclick="save()">Save</button>
  <button onclick="sort_items(true)">Sort by name</button>
  <button onclick="sort_items(false)">Sort by score</button>
`;

test.beforeEach(async ({ page, app }) => {
  await app.load("organize", html);
  await page.evaluate(() => {
    window.usercomics = [
      { id: 1, name: "Zebra &amp; Friends", score: "80", total_votes: 4 },
      { id: 2, name: "beta", score: "90", total_votes: 3 },
      { id: 3, name: "Alpha", score: "90", total_votes: 3 },
      { id: 4, name: "Delta", score: "90", total_votes: 7 },
    ];
    // Only the unrelated Dojo boundary is substituted. Application callbacks,
    // DOM helpers and HTTP requests execute unchanged.
    class Container {
      constructor(id) {
        this.element = document.getElementById(id);
      }
      insertNodes(copy, nodes) {
        for (const node of nodes) node.classList.add("dojoDndItem");
        this.element.append(...nodes);
      }
      selectAll() {}
      deleteSelectedNodes() { this.element.replaceChildren(); }
      clearItems() {}
    }
    window.dojo = {
      dnd: { Source: Container, Target: Container, Avatar: function () {} },
      connect(target, event, callback) {
        target[event] = callback;
        if (event === "onDropExternal") window.trashBoundary = target;
      },
    };
    initDND();
  });
});

test("initial organization preserves IDs and displays names", async ({ page }) => {
  await expect(page.locator("#user_comics .dojoDndItem")).toHaveText(["Zebra & Friends", "beta", "Alpha", "Delta"]);
  expect(await page.locator("#user_comics .dojoDndItem").evaluateAll((nodes) =>
    nodes.map((node) => node.getAttribute("comicid")),
  )).toEqual(["1", "2", "3", "4"]);
});

test("saving sends the current DOM order and hides the success notice after six seconds", async ({ page }) => {
  await freezeClock(page);
  await page.evaluate(() => {
    const list = document.getElementById("user_comics");
    list.prepend(list.lastElementChild);
  });
  const response = await api(page, "save");
  await page.getByRole("button", { name: "Save", exact: true }).click();
  expectPost(await response.request, [["selected", "4,1,2,3"]]);
  await expect(page.locator("#saving_text")).toBeVisible();
  response.release();
  await expect(page.locator("#saving_text")).toBeHidden();
  await expect(page.locator("#saved")).toBeVisible();
  await page.clock.runFor(5999);
  await expect(page.locator("#saved")).toBeVisible();
  await page.clock.runFor(1);
  await expect(page.locator("#saved")).toBeHidden();
});

test("save failure preserves the order and shows an error", async ({ page }) => {
  const response = await api(page, "save", { status: 500 });
  await page.getByRole("button", { name: "Save", exact: true }).click();
  await response.request;
  response.release();
  await expect(page.locator("#save_error")).toBeVisible();
  await expect(page.locator("#saved")).toBeHidden();
  await expect(page.locator("#saving_text")).toBeHidden();
  await expect(page.locator("#user_comics .dojoDndItem")).toHaveCount(4);
});

for (const [label, ids] of [
  ["Sort by name", "3,2,4,1"],
  ["Sort by score", "4,3,2,1"],
]) {
  test(`${label} rerenders and saves with case-insensitive names and score/vote tie-breakers`, async ({ page }) => {
    const response = await api(page, "save");
    await page.getByRole("button", { name: label, exact: true }).click();
    expectPost(await response.request, [["selected", ids]]);
    expect(await page.locator("#user_comics .dojoDndItem").evaluateAll((nodes) =>
      nodes.map((node) => node.getAttribute("comicid")).join(","),
    )).toBe(ids);
    response.release();
    await expect(page.locator("#saved")).toBeVisible();
  });
}

test("an internal drop saves the updated DOM order", async ({ page }) => {
  const response = await api(page, "save");
  await page.evaluate(() => {
    const list = document.getElementById("user_comics");
    list.prepend(list.lastElementChild);
    dojo_usercomics.onDropInternal([], false);
  });
  expectPost(await response.request, [["selected", "4,1,2,3"]]);
  response.release();
  await expect(page.locator("#saved")).toBeVisible();
});

test("a trash drop posts the ID and removes the comic from client state on success", async ({ page }) => {
  const response = await api(page, "remove-list");
  await page.evaluate(() => {
    const node = document.querySelector('[comicid="2"]');
    document.getElementById("trash").append(node);
    trashBoundary.onDropExternal(dojo_usercomics, [node], false);
  });
  expectPost(await response.request, [["ids", "2"]]);
  await expect(page.locator("#saving_text")).toBeVisible();
  response.release();
  await expect(page.locator("#saved")).toBeVisible();
  expect(await page.evaluate(() => usercomics.map((comic) => comic.id))).toEqual([1, 3, 4]);
  await expect(page.locator("#trash .dojoDndItem")).toHaveCount(0);
});

test("trash drop failure shows an error and preserves the client array", async ({ page }) => {
  const response = await api(page, "remove-list", { status: 500 });
  await page.evaluate(() => {
    const node = document.querySelector('[comicid="2"]');
    document.getElementById("trash").append(node);
    trashBoundary.onDropExternal(dojo_usercomics, [node], false);
  });
  await response.request;
  response.release();
  await expect(page.locator("#save_error")).toBeVisible();
  await expect(page.locator("#saving_text")).toBeHidden();
  expect(await page.evaluate(() => usercomics.map((comic) => comic.id))).toEqual([1, 2, 3, 4]);
});

test("saving an empty list sends an empty selection", async ({ page }) => {
  await page.locator("#user_comics").evaluate((list) => list.replaceChildren());
  const response = await api(page, "save");
  await page.getByRole("button", { name: "Save", exact: true }).click();
  expectPost(await response.request, [["selected", ""]]);
  response.release();
  await expect(page.locator("#saved")).toBeVisible();
});

test("a multi-comic trash drop removes every ID from the client array", async ({ page }) => {
  const response = await api(page, "remove-list");
  await page.evaluate(() => {
    const nodes = [2, 3].map((id) => document.querySelector(`[comicid="${id}"]`));
    document.getElementById("trash").append(...nodes);
    trashBoundary.onDropExternal(dojo_usercomics, nodes, false);
  });
  expectPost(await response.request, [["ids", "2,3"]]);
  response.release();
  await expect(page.locator("#saved")).toBeVisible();
  expect(await page.evaluate(() => usercomics.map((comic) => comic.id))).toEqual([1, 4]);
});
