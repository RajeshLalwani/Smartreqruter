(function () {
    const root = document.documentElement;
    const storageKey = "smartrecruit-theme";
    const themeToggle = document.getElementById("theme-toggle");
    const preloader = document.getElementById("thunder-preloader");
    const progressBar = document.getElementById("thunder-progress-bar");
    const progressValue = document.getElementById("thunder-progress-value");
    const statusNode = document.getElementById("preloader-status");
    const themeMeta = document.querySelector('meta[name="theme-color"]');
    const prefersLightQuery = window.matchMedia ? window.matchMedia("(prefers-color-scheme: light)") : null;
    const reducedMotionQuery = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : null;
    const reducedMotion = Boolean(reducedMotionQuery && reducedMotionQuery.matches);
    let deferredInstallPrompt = null;
    let preloaderHidden = false;
    let entranceObserver = null;
    const themes = {
        midnight: {
            name: "Midnight Dark",
            nextLabel: "Activate clean light mode",
            themeColor: "#0a0b10",
        },
        clean: {
            name: "Clean Light",
            nextLabel: "Activate midnight dark mode",
            themeColor: "#f0f2f5",
        },
    };
    const preloaderSteps = [
        { value: 16, text: "Charging recruiter telemetry..." },
        { value: 38, text: "Forging smart-glass surfaces..." },
        { value: 63, text: "Routing live pipeline signals..." },
        { value: 84, text: "Stabilizing dual-theme controls..." },
        { value: 94, text: "Preparing command center..." },
    ];
    function safeStorageGet(key) {
        try {
            return window.localStorage.getItem(key);
        } catch (error) {
            return null;
        }
    }
    function safeStorageSet(key, value) {
        try {
            window.localStorage.setItem(key, value);
        } catch (error) {
            return null;
        }
        return value;
    }
    function normalizeTheme(theme) {
        return theme === "clean" ? "clean" : "midnight";
    }
    function getSystemTheme() {
        return prefersLightQuery && prefersLightQuery.matches ? "clean" : "midnight";
    }
    function updateThemeToggle(theme) {
        if (!themeToggle) {
            return;
        }
        const config = themes[theme];
        const themeState = themeToggle.querySelector(".theme-toggle__state");
        const isClean = theme === "clean";
        themeToggle.setAttribute("aria-pressed", String(isClean));
        themeToggle.setAttribute("aria-label", config.nextLabel);
        if (themeState) {
            themeState.textContent = config.name;
        }
    }
    function applyTheme(theme, options) {
        const settings = options || {};
        const normalizedTheme = normalizeTheme(theme);
        root.setAttribute("data-theme", normalizedTheme);
        root.style.colorScheme = normalizedTheme === "clean" ? "light" : "dark";
        if (themeMeta) {
            themeMeta.setAttribute("content", themes[normalizedTheme].themeColor);
        }
        updateThemeToggle(normalizedTheme);
        if (settings.persist) {
            safeStorageSet(storageKey, normalizedTheme);
        }
    }
    function initializeTheme() {
        const storedTheme = safeStorageGet(storageKey);
        const initialTheme = storedTheme === "clean" || storedTheme === "midnight"
            ? storedTheme
            : root.getAttribute("data-theme") || getSystemTheme();
        applyTheme(initialTheme, { persist: false });
    }
    function bindThemeToggle() {
        if (!themeToggle) {
            return;
        }
        themeToggle.addEventListener("click", function () {
            const currentTheme = normalizeTheme(root.getAttribute("data-theme"));
            const nextTheme = currentTheme === "clean" ? "midnight" : "clean";
            applyTheme(nextTheme, { persist: true });
        });
    }
    function bindSystemThemeSync() {
        if (!prefersLightQuery) {
            return;
        }
        const handleChange = function (event) {
            const storedTheme = safeStorageGet(storageKey);
            if (storedTheme === "clean" || storedTheme === "midnight") {
                return;
            }
            applyTheme(event.matches ? "clean" : "midnight", { persist: false });
        };
        if (prefersLightQuery.addEventListener) {
            prefersLightQuery.addEventListener("change", handleChange);
            return;
        }
        if (prefersLightQuery.addListener) {
            prefersLightQuery.addListener(handleChange);
        }
    }
    function setProgress(value) {
        const clamped = Math.max(0, Math.min(100, Math.round(value)));
        if (progressBar) {
            progressBar.style.width = clamped + "%";
        }
        if (progressValue) {
            progressValue.textContent = clamped + "%";
        }
    }
    function setPreloaderStatus(text) {
        if (statusNode) {
            statusNode.textContent = text;
        }
    }
    function getEntranceNodes() {
        return Array.from(document.querySelectorAll("[data-entrance]"));
    }
    function getMeters(scope) {
        const parent = scope || document;
        return Array.from(parent.querySelectorAll("[data-meter]"));
    }
    function prepareMeters() {
        getMeters().forEach(function (meter) {
            const value = Math.max(0, Math.min(100, Number(meter.getAttribute("data-meter") || 0)));
            meter.dataset.targetWidth = value + "%";
            if (!reducedMotion) {
                meter.style.width = "0%";
                meter.style.willChange = "width";
            }
        });
    }
    function animateMeters(scope, delayBase) {
        const meters = getMeters(scope);
        const baseDelay = typeof delayBase === "number" ? delayBase : 0;
        meters.forEach(function (meter, index) {
            if (meter.dataset.meterAnimated === "true") {
                return;
            }
            meter.dataset.meterAnimated = "true";
            const targetWidth = meter.dataset.targetWidth || "0%";
            if (window.gsap && !reducedMotion) {
                gsap.to(meter, {
                    width: targetWidth,
                    duration: 0.9,
                    delay: baseDelay + (index * 0.05),
                    ease: "power3.out",
                    onComplete: function () {
                        meter.style.removeProperty("will-change");
                    },
                });
                return;
            }
            meter.style.width = targetWidth;
            meter.style.removeProperty("will-change");
        });
    }
    function prepareEntrances() {
        if (reducedMotion) {
            return;
        }
        getEntranceNodes().forEach(function (node) {
            if (node.dataset.entrancePrepared === "true") {
                return;
            }
            node.dataset.entrancePrepared = "true";
            node.style.opacity = "0";
            node.style.transform = "translateY(24px) scale(0.985)";
            node.style.willChange = "opacity, transform";
        });
    }
    function finishEntrance(node) {
        node.classList.add("is-visible");
        node.style.removeProperty("opacity");
        node.style.removeProperty("transform");
        node.style.removeProperty("will-change");
    }
    function animateEntranceNode(node, index) {
        if (node.dataset.entranceAnimated === "true") {
            return;
        }
        node.dataset.entranceAnimated = "true";
        const delay = Math.max(0, index || 0) * 0.06;
        if (window.gsap && !reducedMotion) {
            gsap.to(node, {
                autoAlpha: 1,
                y: 0,
                scale: 1,
                duration: 0.82,
                delay: delay,
                ease: "back.out(1.15)",
                clearProps: "opacity,visibility,transform,will-change",
                onComplete: function () {
                    node.classList.add("is-visible");
                },
            });
        } else if (reducedMotion) {
            finishEntrance(node);
        } else {
            window.setTimeout(function () {
                node.classList.add("is-visible");
                finishEntrance(node);
            }, delay * 1000);
        }
        animateMeters(node, delay + 0.08);
    }
    function revealEntrances() {
        const nodes = getEntranceNodes();
        if (!nodes.length) {
            animateMeters();
            return;
        }
        if (reducedMotion) {
            nodes.forEach(finishEntrance);
            animateMeters();
            return;
        }
        if ("IntersectionObserver" in window) {
            entranceObserver = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (!entry.isIntersecting) {
                        return;
                    }
                    animateEntranceNode(entry.target, 0);
                    entranceObserver.unobserve(entry.target);
                });
            }, {
                threshold: 0.18,
                rootMargin: "0px 0px -10% 0px",
            });
            nodes.forEach(function (node) {
                entranceObserver.observe(node);
            });
            window.requestAnimationFrame(function () {
                nodes.forEach(function (node, index) {
                    if (node.dataset.entranceAnimated === "true") {
                        return;
                    }
                    const rect = node.getBoundingClientRect();
                    if (rect.top < (window.innerHeight * 0.92)) {
                        animateEntranceNode(node, index);
                        entranceObserver.unobserve(node);
                    }
                });
            });
            return;
        }
        nodes.forEach(function (node, index) {
            animateEntranceNode(node, index);
        });
    }
    function clearBootFallback() {
        if (window.__smartRecruitBootFallback) {
            window.clearTimeout(window.__smartRecruitBootFallback);
            window.__smartRecruitBootFallback = null;
        }
    }
    function hidePreloader() {
        if (preloaderHidden) {
            return;
        }
        preloaderHidden = true;
        clearBootFallback();
        root.classList.remove("preloader-active");
        if (!preloader) {
            revealEntrances();
            return;
        }
        preloader.classList.add("is-hidden");
        preloader.setAttribute("aria-hidden", "true");
        window.setTimeout(function () {
            preloader.style.display = "none";
            revealEntrances();
        }, reducedMotion ? 40 : 420);
    }
    function runPreloader() {
        prepareEntrances();
        prepareMeters();
        if (!preloader || !progressBar || !statusNode) {
            hidePreloader();
            return;
        }
        root.classList.add("preloader-active");
        let timer = null;
        let stepIndex = 0;
        let finished = false;
        let startTime = Date.now();
        function advance() {
            if (finished || stepIndex >= preloaderSteps.length) {
                return;
            }
            const step = preloaderSteps[stepIndex];
            setProgress(step.value);
            setPreloaderStatus(step.text);
            stepIndex += 1;
            timer = window.setTimeout(advance, reducedMotion ? 60 : 400);
        }
        function finish() {
            if (finished) {
                return;
            }
            let elapsed = Date.now() - startTime;
            let minTime = reducedMotion ? 100 : 2500;
            if (elapsed < minTime) {
                window.setTimeout(finish, minTime - elapsed);
                return;
            }
            finished = true;
            if (timer) {
                window.clearTimeout(timer);
            }
            setProgress(100);
            setPreloaderStatus("Interface online.");
            window.setTimeout(hidePreloader, reducedMotion ? 20 : 400);
        }
        advance();
        if (document.readyState === "complete") {
            finish();
        } else {
            window.addEventListener("load", finish, { once: true });
        }
        window.setTimeout(finish, reducedMotion ? 180 : 4000);
        window.addEventListener("pageshow", function (event) {
            if (event.persisted) {
                finish();
            }
        });
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
    function init() {
        initializeTheme();
        bindThemeToggle();
        bindSystemThemeSync();
        bindPwaInstallPrompt();
        runPreloader();
    }
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init, { once: true });
    } else {
        init();
    }
})();
