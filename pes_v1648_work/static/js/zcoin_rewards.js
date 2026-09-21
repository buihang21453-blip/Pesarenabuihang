(function () {
    "use strict";

    function formatNumber(value) {
        return new Intl.NumberFormat("vi-VN").format(Number(value || 0));
    }

    function closeRewardOverlay(overlay) {
        if (!overlay) return;
        overlay.classList.add("is-closing");
        window.setTimeout(function () { overlay.remove(); }, 220);
    }

    function createConfetti(layer) {
        const colors = ["#f8c43a", "#fff0a3", "#2dd17e", "#4f9cff", "#ff7a82"];
        for (let index = 0; index < 72; index += 1) {
            const piece = document.createElement("i");
            piece.className = "zcoin-confetti";
            piece.style.left = Math.random() * 100 + "%";
            piece.style.background = colors[index % colors.length];
            piece.style.setProperty("--duration", (1.7 + Math.random() * 1.7) + "s");
            piece.style.setProperty("--delay", (Math.random() * 0.45) + "s");
            piece.style.setProperty("--drift", ((Math.random() - 0.5) * 220) + "px");
            piece.style.setProperty("--rotate", (Math.random() * 180) + "deg");
            layer.appendChild(piece);
        }
    }

    function showRewardEffect(data) {
        if (!data || !Number(data.amount)) return;
        const overlay = document.createElement("div");
        overlay.className = "zcoin-reward-overlay";
        overlay.innerHTML = [
            '<div class="zcoin-confetti-layer"></div>',
            '<section class="zcoin-reward-popup" role="dialog" aria-modal="true" aria-label="Nhận Zcoin thành công">',
            '<img src="' + ((window.PES_ASSET_BASE_URL || '/static').replace(/\/$/, '') + '/zcoin-logo.webp') + '" alt="Zcoin">',
            '<h2></h2>',
            '<strong class="zcoin-reward-amount"></strong>',
            '<p></p>',
            '<button class="btn gold" type="button">Tuyệt vời</button>',
            '</section>'
        ].join("");
        overlay.querySelector("h2").textContent = data.title || "Nhận Zcoin thành công!";
        overlay.querySelector(".zcoin-reward-amount").textContent = "+" + formatNumber(data.amount) + " Zcoin";
        overlay.querySelector("p").textContent = data.type === "daily_checkin"
            ? "Chuỗi điểm danh: ngày " + Number(data.streak_day || 1) + "/7"
            : "Gift Code: " + String(data.code || "");
        overlay.querySelector("button").addEventListener("click", function () { closeRewardOverlay(overlay); });
        overlay.addEventListener("click", function (event) {
            if (event.target === overlay) closeRewardOverlay(overlay);
        });
        document.addEventListener("keydown", function onEscape(event) {
            if (event.key === "Escape" && document.body.contains(overlay)) {
                closeRewardOverlay(overlay);
                document.removeEventListener("keydown", onEscape);
            }
        });
        document.body.appendChild(overlay);
        createConfetti(overlay.querySelector(".zcoin-confetti-layer"));
    }

    document.addEventListener("DOMContentLoaded", function () {
        const input = document.getElementById("giftCodeInput");
        if (input) {
            input.addEventListener("input", function () {
                input.value = input.value.toUpperCase().replace(/\s+/g, "");
            });
        }
        const dataNode = document.getElementById("zcoinRewardEffectData");
        if (!dataNode) return;
        try { showRewardEffect(JSON.parse(dataNode.textContent || "{}")); }
        catch (error) { console.warn("Không thể chạy hiệu ứng Zcoin", error); }
    });
})();
