export const getExtensionUrl = (path) => {
    try {
        if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.getURL) {
            return chrome.runtime.getURL(path);
        }
    } catch (e) {
        // This catch specifically handles the "Extension context invalidated" error
        // which triggers if the extension is recompiled/reloaded but the host webpage is not refreshed.
        console.warn("COS: Extension context invalidated. Please reload the page.");
    }
    return `/${path}`;
};
