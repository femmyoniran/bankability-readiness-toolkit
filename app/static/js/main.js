/* ============================================================
   Bankability Assessment Toolkit - Main JavaScript
   ============================================================ */

(function () {
    "use strict";

    // Auto-dismiss flash messages after 6 seconds
    document.addEventListener("DOMContentLoaded", function () {
        var flashes = document.querySelectorAll(".flash");
        flashes.forEach(function (el) {
            setTimeout(function () {
                el.style.transition = "opacity 0.3s";
                el.style.opacity = "0";
                setTimeout(function () { el.remove(); }, 300);
            }, 6000);
        });
    });

    // Smooth scroll for internal links
    document.addEventListener("click", function (e) {
        var link = e.target.closest("a[href^='#']");
        if (link) {
            var targetId = link.getAttribute("href").slice(1);
            var targetEl = document.getElementById(targetId);
            if (targetEl) {
                e.preventDefault();
                targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        }
    });

    // Utility: format number as USD
    window.formatCurrency = function (value) {
        if (value === null || value === undefined || isNaN(value)) return "N/A";
        return "$" + Number(value).toLocaleString("en-US", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    };

    // Utility: format percentage
    window.formatPercent = function (value, decimals) {
        if (value === null || value === undefined || isNaN(value)) return "N/A";
        return Number(value).toFixed(decimals || 1) + "%";
    };

})();
