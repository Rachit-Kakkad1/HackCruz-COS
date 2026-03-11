document.getElementById("acceptBtn").addEventListener("click", () => {
  chrome.storage.local.set({ consent: true }, () => {
    // Optionally alert the user or redirect them.
    window.close();
  });
});

document.getElementById("declineBtn").addEventListener("click", () => {
  chrome.storage.local.set({ consent: false }, () => {
    alert("COS will not monitor activity.");
    window.close();
  });
});
