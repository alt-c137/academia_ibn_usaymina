/* ============================================================
   Главный скрипт платформы (vanilla JS, без библиотек).

   1. Тема оформления: «Классика» / «Минимал» — cookie + data-theme
   2. Мобильное меню (бургер)
   3. Появление блоков при прокрутке (reveal)
   4. Кольца прогресса 70/25/5 (заполнение conic-gradient)
   5. Кнопки печати выписки
   ============================================================ */
(function () {
    "use strict";

    document.documentElement.classList.add("js");

    /* --- 1. Тема оформления ------------------------------------ */
    var THEME_COOKIE = "theme";

    function markActiveButtons(theme) {
        var buttons = document.querySelectorAll(".theme-switch__btn");
        buttons.forEach(function (btn) {
            btn.classList.toggle("is-active", btn.dataset.setTheme === theme);
        });
    }

    function setTheme(theme) {
        document.documentElement.dataset.theme = theme;
        // cookie читает сервер (apps/core/middleware.py) — тема не «мигает» при загрузке
        document.cookie =
            THEME_COOKIE + "=" + theme + "; path=/; max-age=31536000; samesite=lax";
        markActiveButtons(theme);
    }

    markActiveButtons(document.documentElement.dataset.theme || "paper");

    document.querySelectorAll(".theme-switch__btn").forEach(function (btn) {
        btn.addEventListener("click", function () {
            setTheme(btn.dataset.setTheme);
        });
    });

    /* --- 2. Мобильное меню -------------------------------------- */
    var burger = document.getElementById("burger");
    var header = document.querySelector(".site-header");
    if (burger && header) {
        burger.addEventListener("click", function () {
            header.classList.toggle("nav-open");
        });
    }

    /* --- 3. Появление блоков при прокрутке ---------------------- */
    var revealItems = document.querySelectorAll(".reveal");
    if ("IntersectionObserver" in window && revealItems.length) {
        var observer = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("is-visible");
                        observer.unobserve(entry.target);
                    }
                });
            },
            { rootMargin: "0px 0px -8% 0px", threshold: 0.05 }
        );
        revealItems.forEach(function (item) {
            observer.observe(item);
        });
    } else {
        revealItems.forEach(function (item) {
            item.classList.add("is-visible");
        });
    }

    /* --- 4. Кольца прогресса ------------------------------------ */
    document.querySelectorAll(".ring").forEach(function (ring) {
        var value = parseInt(ring.dataset.value, 10);
        if (!isNaN(value)) {
            ring.style.setProperty("--p", value);
        }
    });

    /* --- 5. Кнопка печати выписки -------------------------------- */
    document.addEventListener("click", function (event) {
        var btn = event.target.closest("[data-print]");
        if (!btn) return;
        document.body.classList.add("print-doc");
        window.print();
        // afterprint сработает и при отмене печати
        window.addEventListener("afterprint", function () {
            document.body.classList.remove("print-doc");
        }, { once: true });
    });
})();
