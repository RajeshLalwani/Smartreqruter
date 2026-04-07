(function () {
    const root = document.documentElement;
    const storageKey = "smartrecruit-theme";
    const preloader = document.getElementById("thunder-preloader");
    const progressBar = document.getElementById("thunder-progress-bar");
    const statusNode = document.getElementById("preloader-status");
    const themeToggle = document.getElementById("theme-toggle");
    let deferredInstallPrompt = null;
    const statusSteps = [
        { value: 16, text: "Calibrating glass layers..." },
        { value: 38, text: "Routing recruiter telemetry..." },
        { value: 63, text: "Charging thunder accents..." },
        { value: 84, text: "Synchronizing dashboard modules..." },
        { value: 100, text: "System ready." },
    ];

    function setTheme(theme) {
        const normalized = theme === "clean" ? "clean" : "midnight";
        root.setAttribute("data-theme", normalized);
        localStorage.setItem(storageKey, normalized);
        const themeColor = normalized === "clean" ? "#f0f2f5" : "#0a0b10";
        const metaTheme = document.querySelector('meta[name="theme-color"]');
        if (metaTheme) {
            metaTheme.setAttribute("content", themeColor);
        }
    }

    function initTheme() {
        const storedTheme = localStorage.getItem(storageKey);
        if (storedTheme) {
            setTheme(storedTheme);
            return;
        }
        const prefersLight = window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches;
        setTheme(prefersLight ? "clean" : "midnight");
    }

    function bindThemeToggle() {
        if (!themeToggle) {
            return;
        }
        themeToggle.addEventListener("click", function () {
            const nextTheme = root.getAttribute("data-theme") === "clean" ? "midnight" : "clean";
            setTheme(nextTheme);
        });
    }

    function animateEntrance() {
        const nodes = Array.from(document.querySelectorAll("[data-entrance]"));
        if (!nodes.length) {
            return;
        }
        if (window.gsap) {
            gsap.set(nodes, { opacity: 0, y: 18, scale: 0.985 });
            gsap.to(nodes, {
                opacity: 1,
                y: 0,
                scale: 1,
                duration: 0.72,
                ease: "back.out(1.18)",
                stagger: 0.08,
                clearProps: "all",
            });
            return;
        }
        nodes.forEach(function (node, index) {
            window.setTimeout(function () {
                node.classList.add("entrance-ready");
            }, index * 70);
        });
    }

    function hidePreloader() {
        if (!preloader) {
            animateEntrance();
            return;
        }
        preloader.classList.add("is-hidden");
        window.setTimeout(function () {
            preloader.style.display = "none";
            animateEntrance();
        }, 420);
    }

    function runPreloader() {
        if (!preloader || !progressBar || !statusNode) {
            return;
        }

        let stepIndex = 0;
        function advance() {
            if (stepIndex >= statusSteps.length) {
                hidePreloader();
                return;
            }
            const step = statusSteps[stepIndex];
            progressBar.style.width = step.value + "%";
            statusNode.textContent = step.text;
            stepIndex += 1;
            window.setTimeout(advance, step.value === 100 ? 320 : 220);
        }

        advance();
        window.addEventListener("load", function () {
            window.setTimeout(function () {
                progressBar.style.width = "100%";
                statusNode.textContent = "Interface online.";
                hidePreloader();
            }, 320);
        }, { once: true });
    }

    function bindPwaInstallPrompt() {
        window.addEventListener("beforeinstallprompt", function (event) {
            event.preventDefault();
            deferredInstallPrompt = event;
        });

        window.installPWA = async function () {
            if (!deferredInstallPrompt) {
                return false;
            }
            deferredInstallPrompt.prompt();
            await deferredInstallPrompt.userChoice;
            deferredInstallPrompt = null;
            return true;
        };
    }

    document.addEventListener("DOMContentLoaded", function () {
        initTheme();
        bindThemeToggle();
        bindPwaInstallPrompt();
        runPreloader();
        if (document.readyState === "complete") {
            hidePreloader();
        }
    });
})();
