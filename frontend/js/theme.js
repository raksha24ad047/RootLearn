(function () {
    const STORAGE_KEY = "rootlearn_theme";

    function updateToggleUI(theme) {
        const isDark = theme === "dark";
        const btn = document.getElementById("themeToggleBtn");
        const icon = document.getElementById("themeToggleIcon");
        const text = document.getElementById("themeToggleText");

        if (btn) btn.setAttribute("aria-pressed", String(isDark));
        if (icon) icon.textContent = isDark ? "☀" : "☾";
        if (text) text.textContent = isDark ? "Light" : "Dark";
    }

    function setTheme(theme) {
        const mode = theme === "dark" ? "dark" : "light";
        document.documentElement.setAttribute("data-theme", mode);
        if (document.body) {
            document.body.setAttribute("data-theme", mode);
        }
        try {
            localStorage.setItem(STORAGE_KEY, mode);
        } catch (_) {}
        updateToggleUI(mode);
    }

    function bindToggle() {
        let saved = "light";
        try {
            saved = localStorage.getItem(STORAGE_KEY) || "light";
        } catch (_) {}
        setTheme(saved);

        document.addEventListener("click", function (event) {
            const btn = event.target.closest("#themeToggleBtn, [data-theme-toggle]");
            if (!btn) return;
            const current = document.documentElement.getAttribute("data-theme") || "light";
            setTheme(current === "dark" ? "light" : "dark");
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bindToggle);
    } else {
        bindToggle();
    }
})();