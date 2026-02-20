/* ============================================================
   Bankability Assessment Toolkit - Form Helpers
   ============================================================ */

(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        initConditionalFields();
        initFormValidation();
        initNumericFormatting();
    });

    /**
     * Show/hide fields based on technology type selection.
     */
    function initConditionalFields() {
        var techSelect = document.getElementById("technology_type");
        if (!techSelect) return;

        techSelect.addEventListener("change", function () {
            var value = this.value.toLowerCase();
            var solarFields = document.querySelectorAll(".solar-only");
            var windFields = document.querySelectorAll(".wind-only");
            var storageFields = document.querySelectorAll(".storage-only");

            solarFields.forEach(function (el) {
                el.style.display = value.indexOf("solar") >= 0 ? "block" : "none";
            });
            windFields.forEach(function (el) {
                el.style.display = value.indexOf("wind") >= 0 ? "block" : "none";
            });
            storageFields.forEach(function (el) {
                el.style.display = value.indexOf("storage") >= 0 || value.indexOf("battery") >= 0 ? "block" : "none";
            });
        });
    }

    /**
     * Basic client-side validation before submit.
     */
    function initFormValidation() {
        var form = document.querySelector("form.project-form");
        if (!form) return;

        form.addEventListener("submit", function (e) {
            var required = form.querySelectorAll("[required]");
            var errors = [];

            required.forEach(function (field) {
                if (!field.value || field.value.trim() === "") {
                    errors.push(field.getAttribute("name") || field.id);
                    field.style.borderColor = "#b22222";
                } else {
                    field.style.borderColor = "";
                }
            });

            if (errors.length > 0) {
                e.preventDefault();
                var first = form.querySelector("[name='" + errors[0] + "']") || form.querySelector("#" + errors[0]);
                if (first) {
                    first.scrollIntoView({ behavior: "smooth", block: "center" });
                    first.focus();
                }
            }
        });
    }

    /**
     * Format numeric inputs with commas on blur (visual only -- raw value submitted).
     */
    function initNumericFormatting() {
        var numericFields = document.querySelectorAll("input[type='number']");
        numericFields.forEach(function (field) {
            field.addEventListener("blur", function () {
                // Remove validation styling on correction
                if (this.value) {
                    this.style.borderColor = "";
                }
            });
        });
    }

})();
