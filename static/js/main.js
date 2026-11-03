/* ==========================================================================
   softly, mia ♡ — small interactions, no frameworks
   ========================================================================== */

(function () {
    "use strict";

    var storageLangKey = "mia-lang";
    var storageLikesKey = "softly-mia-liked";
    var body = document.body;
    var lang = body ? body.dataset.lang : "en";
    var labels = window.MIA || {};

    /* ---------------------------------------------------------------------
       1. Remember the language (localStorage + a cookie fallback)
       --------------------------------------------------------------------- */

    try {
        if (lang === "en" || lang === "ru") {
            localStorage.setItem(storageLangKey, lang);
            document.cookie = "mia_lang=" + lang + "; path=/; max-age=31536000; SameSite=Lax";
        }
    } catch (error) {
        // Private mode can block storage. The site still works.
    }

    /* ---------------------------------------------------------------------
       2. Mobile menu
       --------------------------------------------------------------------- */

    var header = document.querySelector("[data-header]");
    var menuToggle = document.querySelector("[data-menu-toggle]");
    var nav = document.getElementById("site-nav");
    var menuLabel = document.querySelector("[data-menu-label]");

    function setMenu(open) {
        if (!header || !menuToggle) return;
        header.classList.toggle("nav-open", open);
        menuToggle.setAttribute("aria-expanded", open ? "true" : "false");

        if (menuLabel) {
            menuLabel.textContent = open
                ? menuLabel.dataset.close || "Close"
                : menuLabel.dataset.open || "Menu";
        }
    }

    if (menuToggle && nav) {
        menuToggle.addEventListener("click", function () {
            setMenu(!header.classList.contains("nav-open"));
        });

        nav.querySelectorAll("a").forEach(function (link) {
            link.addEventListener("click", function () {
                setMenu(false);
            });
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") setMenu(false);
        });

        document.addEventListener("click", function (event) {
            if (!header.classList.contains("nav-open")) return;
            if (!header.contains(event.target)) setMenu(false);
        });

        var desktopQuery = window.matchMedia("(min-width: 861px)");
        if (desktopQuery.addEventListener) {
            desktopQuery.addEventListener("change", function (event) {
                if (event.matches) setMenu(false);
            });
        }
    }

    /* ---------------------------------------------------------------------
       3. A little shadow when the page scrolls
       --------------------------------------------------------------------- */

    if (header) {
        var setHeaderState = function () {
            header.classList.toggle("is-scrolled", window.scrollY > 8);
        };
        setHeaderState();
        window.addEventListener("scroll", setHeaderState, { passive: true });
    }

    /* ---------------------------------------------------------------------
       4. Gentle reveal animations
       --------------------------------------------------------------------- */

    var revealItems = Array.prototype.slice.call(document.querySelectorAll(".reveal"));
    var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function showAllReveals() {
        revealItems.forEach(function (item) {
            item.classList.add("is-visible");
        });
    }

    if (!revealItems.length) {
        // Nothing to animate.
    } else if (reduceMotion || !("IntersectionObserver" in window)) {
        showAllReveals();
    } else {
        revealItems.forEach(function (item, index) {
            item.style.transitionDelay = (index % 4) * 65 + "ms";
        });

        var observer = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("is-visible");
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.08, rootMargin: "0px 0px -35px 0px" }
        );

        revealItems.forEach(function (item) {
            observer.observe(item);
        });
    }

    /* ---------------------------------------------------------------------
       5. Likes: database total + this browser's state
       --------------------------------------------------------------------- */

    function readLikedSlugs() {
        try {
            var saved = JSON.parse(localStorage.getItem(storageLikesKey) || "[]");
            return new Set(Array.isArray(saved) ? saved : []);
        } catch (error) {
            return new Set();
        }
    }

    function saveLikedSlugs(liked) {
        try {
            localStorage.setItem(storageLikesKey, JSON.stringify(Array.from(liked)));
        } catch (error) {
            // Storage can be unavailable; the click still updates the database.
        }
    }

    var likedSlugs = readLikedSlugs();
    var likeButtons = Array.prototype.slice.call(document.querySelectorAll("[data-like-button]"));

    likeButtons.forEach(function (button) {
        var slug = button.dataset.slug;
        var countElement = button.querySelector("[data-like-count]");
        var heart = button.querySelector(".like-heart");

        function render(isLiked, count) {
            if (typeof count === "number" && !Number.isNaN(count)) {
                button.dataset.likes = String(count);
                if (countElement) countElement.textContent = String(count);
            }

            button.classList.toggle("is-liked", isLiked);
            button.setAttribute("aria-pressed", isLiked ? "true" : "false");

            var currentCount = button.dataset.likes || "0";
            var actionLabel = isLiked
                ? labels.unlikeLabel || "Remove your like"
                : labels.likeLabel || "Like this post";
            var label = actionLabel + " — " + currentCount + " " + (labels.likesWord || "likes");
            button.setAttribute("aria-label", label);
            button.setAttribute("title", actionLabel);

            if (heart) heart.textContent = isLiked ? "♥" : "♡";
        }

        render(likedSlugs.has(slug), Number(button.dataset.likes));

        button.addEventListener("click", function () {
            if (button.dataset.busy === "1") return;

            var willLike = !likedSlugs.has(slug);
            button.dataset.busy = "1";
            button.classList.add("is-busy");
            button.setAttribute("aria-busy", "true");

            fetch(button.dataset.endpoint, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify({ action: willLike ? "like" : "unlike" })
            })
                .then(function (response) {
                    if (!response.ok) throw new Error("Like request failed");
                    return response.json();
                })
                .then(function (data) {
                    if (willLike) {
                        likedSlugs.add(slug);
                    } else {
                        likedSlugs.delete(slug);
                    }
                    saveLikedSlugs(likedSlugs);
                    render(willLike, Number(data.likes));

                    button.classList.remove("like-error");
                    button.classList.add("like-pop");
                    window.setTimeout(function () {
                        button.classList.remove("like-pop");
                    }, 480);
                })
                .catch(function () {
                    button.classList.add("like-error");
                    window.setTimeout(function () {
                        button.classList.remove("like-error");
                    }, 2200);
                })
                .finally(function () {
                    button.dataset.busy = "0";
                    button.classList.remove("is-busy");
                    button.removeAttribute("aria-busy");
                });
        });
    });

    /* ---------------------------------------------------------------------
       6. Character counter for Dear Mia
       --------------------------------------------------------------------- */

    var messageField = document.querySelector("[data-message]");
    var counter = document.querySelector("[data-counter]");

    if (messageField && counter) {
        var updateCounter = function () {
            counter.textContent = messageField.value.length + " / 1000";
        };
        updateCounter();
        messageField.addEventListener("input", updateCounter);
    }

    /* ---------------------------------------------------------------------
       7. A calmer submit button
       --------------------------------------------------------------------- */

    var noteForm = document.querySelector("[data-note-form]");
    if (noteForm) {
        noteForm.addEventListener("submit", function () {
            var submit = noteForm.querySelector("[data-submit]");
            if (!submit) return;
            submit.disabled = true;
            if (labels.sendingLabel) submit.textContent = labels.sendingLabel;
        });
    }
})();
