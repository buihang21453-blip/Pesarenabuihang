(function () {
    "use strict";

    function getAccountMenuElements() {
        return {
            button: document.getElementById("accountMenuButton"),
            dropdown: document.getElementById("accountDropdown")
        };
    }

    function setAccountMenuOpen(isOpen) {
        const elements = getAccountMenuElements();
        if (!elements.button || !elements.dropdown) return;

        elements.dropdown.hidden = !isOpen;
        elements.button.setAttribute("aria-expanded", isOpen ? "true" : "false");
        elements.button.classList.toggle("is-open", isOpen);
    }

    window.toggleAccountMenu = function (event) {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }

        const elements = getAccountMenuElements();
        if (!elements.button || !elements.dropdown) return;
        setAccountMenuOpen(elements.dropdown.hidden);
    };

    document.addEventListener("DOMContentLoaded", function () {
        const elements = getAccountMenuElements();

        if (elements.button && elements.dropdown) {
            elements.dropdown.addEventListener("click", function (event) {
                event.stopPropagation();
            });

            document.addEventListener("click", function (event) {
                if (!elements.dropdown.hidden && !elements.button.contains(event.target) && !elements.dropdown.contains(event.target)) {
                    setAccountMenuOpen(false);
                }
            });

            document.addEventListener("keydown", function (event) {
                if (event.key !== "Escape" || elements.dropdown.hidden) return;
                setAccountMenuOpen(false);
                elements.button.focus();
            });
        }

        const search = document.getElementById("zcoinPlayerSearch");
        if (!search) return;

        search.addEventListener("input", function () {
            const query = search.value.trim().toLowerCase();
            document.querySelectorAll("[data-zcoin-player]").forEach(function (row) {
                row.hidden = Boolean(query) && !(row.dataset.search || "").includes(query);
            });
        });
    });
})();
