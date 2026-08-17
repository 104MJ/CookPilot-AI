(function () {
  const STORAGE_KEY = "cookpilot-theme";
  const root = document.documentElement;

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    const toggle = document.querySelector("[data-theme-toggle]");
    const icon = document.querySelector("[data-theme-icon]");
    if (toggle) {
      toggle.setAttribute("aria-label", theme === "dark" ? "Passer en thème clair" : "Passer en thème sombre");
    }
    if (icon) {
      icon.src = `https://unpkg.com/lucide-static@latest/icons/${theme === "dark" ? "sun" : "moon"}.svg`;
    }
  }

  const stored = localStorage.getItem(STORAGE_KEY);
  const preferred = stored || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  applyTheme(preferred);

  document.addEventListener("click", function (event) {
    const toggle = event.target.closest("[data-theme-toggle]");
    if (!toggle) return;
    const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    localStorage.setItem(STORAGE_KEY, next);
    applyTheme(next);
  });
})();
