/* ============================================================
   Таймер теста: отсчёт от data-seconds-left, автосдача на нуле.
   ============================================================ */
(function () {
    "use strict";

    var timer = document.querySelector(".exam-timer");
    var form = document.getElementById("exam-form");
    if (!timer || !form) return;

    var secondsLeft = parseInt(timer.dataset.secondsLeft, 10);
    if (isNaN(secondsLeft)) return;

    var valueEl = timer.querySelector(".exam-timer__value");
    var submitted = false;

    function submitForm() {
        if (submitted) return;
        submitted = true;
        form.submit();
    }

    function pad(n) {
        return n < 10 ? "0" + n : String(n);
    }

    function render() {
        var minutes = Math.floor(secondsLeft / 60);
        var seconds = secondsLeft % 60;
        valueEl.textContent = pad(minutes) + ":" + pad(seconds);
        if (secondsLeft <= 60) {
            timer.classList.add("is-danger");
        }
    }

    render();
    var interval = setInterval(function () {
        secondsLeft -= 1;
        if (secondsLeft <= 0) {
            clearInterval(interval);
            valueEl.textContent = "00:00";
            submitForm(); // время вышло — отправляем то, что отмечено
            return;
        }
        render();
    }, 1000);

    // Подстраховка от двойной отправки: кнопкой и таймером одновременно
    form.addEventListener("submit", function () {
        submitted = true;
    });
})();
