/**
 * COS — Content Script.
 *
 * Listens for messages from the background service worker and
 * responds with visible text from the current page.
 */

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "GET_PAGE_TEXT") {
    const text = document.body ? document.body.innerText.slice(0, 2000) : "";
    sendResponse({ text });
  }
  return true; // keep message channel open for async response
});
