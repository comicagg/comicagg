/*jslint white: true, onevar: true, undef: true, nomen: true, eqeqeq: true, plusplus: true, bitwise: true, regexp: true, newcap: true, immed: true, strict: true */
/*global document, window, fetch, URL, URLSearchParams, url_forget_new_blogs, titlei18n, titlebase, unreadCounter: true, comicCounter: true, newComicCounter: true, newsCounter: true*/
"use strict";

function byId(id) {
  return document.getElementById(id);
}

function showElement(element) {
  element.style.display = "";
}

function hideElement(element) {
  element.style.display = "none";
}

function isVisible(element) {
  return element.style.display !== "none";
}

// Position relative to the document, independent of the current scroll
function documentOffset(element) {
  const rect = element.getBoundingClientRect();
  return { top: rect.top + window.scrollY, left: rect.left + window.scrollX };
}

// Scrolls to the element (or element id) plus an extra offset
function scrollToExtra(element, n) {
  if (typeof element === "string") {
    element = byId(element);
  }
  const pos = documentOffset(element);
  window.scrollTo(pos.left, pos.top + n);
  return element;
}

function getCookie(name) {
  const prefix = name + "=";
  for (const cookie of document.cookie.split(";")) {
    const trimmed = cookie.trim();
    if (trimmed.startsWith(prefix)) {
      return decodeURIComponent(trimmed.substring(prefix.length));
    }
  }
  return null;
}

function isSameOrigin(url) {
  return new URL(url, document.location.href).origin === document.location.origin;
}

function focusOnLogin() {
  byId("id_username").focus();
}

function openurl(url, target = "_blank") {
  window.open(url, target);
  return false;
}

// Sends the parameters (key-value, arrays allowed) as a query string for GET
// or as a form-encoded body otherwise. Same-origin unsafe requests get the CSRF token.
async function startRequest(url, options) {
  // set as default data type "json"
  const dataType = options.dataType || "json";
  const method = (options.method || "get").toUpperCase();
  const sameOrigin = isSameOrigin(url);
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(options.parameters || {})) {
    for (const item of Array.isArray(value) ? value : [value]) {
      params.append(key, item ?? "");
    }
  }

  const headers = {};
  const init = { method: method, headers: headers };
  if (sameOrigin) {
    headers["X-Requested-With"] = "XMLHttpRequest";
  }
  if (method === "GET" || method === "HEAD") {
    const query = params.toString();
    if (query) {
      url += (url.includes("?") ? "&" : "?") + query;
    }
  } else {
    init.body = params;
    const token = getCookie("csrftoken");
    if (sameOrigin && token !== null) {
      headers["X-CSRFToken"] = token;
    }
  }

  let data;
  try {
    const response = await fetch(url, init);
    if (!response.ok) {
      throw new Error("HTTP " + response.status);
    }
    data = dataType === "json" ? await response.json() : await response.text();
  } catch (error) {
    if (typeof options.onFailure === "function") {
      options.onFailure(error);
    }
    return;
  }
  if (typeof options.onSuccess === "function") {
    options.onSuccess(data);
  }
}

function removeComicId(array, comicid) {
  var found = false,
    i,
    len,
    comic;
  for (i = 0, len = array.length; i < len && !found; i += 1) {
    comic = array[i];
    found = comic !== undefined && comic !== null && comic.id === comicid;
    if (found) {
      array[i] = undefined;
    }
  }
  return found ? comic : found;
}

// updates html counters
function updateCounters(counters) {
  if (typeof counters !== "undefined") {
    unreadCounter = counters.unreads;
    comicCounter = counters.comics;
    newComicCounter = counters.new_comics;
    newsCounter = counters.news;
  } else {
    return;
  }
  //first update the counters in the menu
  if (counters.unreads > 0) {
    byId("menuUnreadCounter").textContent = " (" + counters.unreads + ")";
  } else {
    hideElement(byId("menuUnreadCounter"));
    if (byId("mark_all_read")) {
      hideElement(byId("mark_all_read"));
    }
  }
  if (counters.new_comics > 0) {
    byId("menuNewComicCounter").textContent = " (" + counters.new_comics + ")";
  } else {
    hideElement(byId("menuNewComicCounter"));
  }
  if (counters.news > 0) {
    byId("menuNewsCounter").textContent = " (" + counters.news + ")";
  } else {
    hideElement(byId("menuNewsCounter"));
  }
  //if we're in the read page
  if (typeof titlei18n === "string") {
    if (counters.unreads > 0) {
      document.title = titlei18n + " (" + counters.unreads + ") - " + titlebase;
      hideElement(byId("noUnreadCounters"));
      showElement(byId("unreadCounters"));
      byId("unreadCountersUnread").textContent = counters.unreads;
      byId("unreadCountersTotal").textContent = counters.comics;
    } else {
      document.title = titlei18n + " - " + titlebase;
      showElement(byId("noUnreadCounters"));
      hideElement(byId("unreadCounters"));
      byId("noUnreadCountersTotal").textContent = counters.comics;
    }
  }
  return 0;
}

/********/
/* Blog */
/********/

function forget_news() {
  startRequest(url_forget_new_blogs, {
    method: "post",
    onSuccess: function (counters) {
      updateCounters(counters);
    },
    onFailure: function (response) {},
  });
}
