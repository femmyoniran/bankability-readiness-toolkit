/* ============================================================
   Bankability Assessment Toolkit - Chart.js Chart Rendering
   ============================================================ */

(function () {
    "use strict";

    var COLORS = {
        primary: "#1b365d",
        primaryLight: "#2c5282",
        secondary: "#2a7f62",
        accent: "#c97b1a",
        danger: "#b22222",
        blue: "rgba(44,82,130,0.7)",
        blueFill: "rgba(44,82,130,0.15)",
        green: "rgba(42,127,98,0.7)",
        greenFill: "rgba(42,127,98,0.15)",
        orange: "rgba(201,123,26,0.7)",
        red: "rgba(178,34,34,0.7)"
    };

    var chartDefaults = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: "top",
                labels: { font: { size: 11 }, padding: 12 }
            }
        }
    };

    /**
     * Initialize all results-page charts.
     * Called from results.html with cashFlows and subScores data.
     */
    window.initResultsCharts = function (cashFlows, subScores) {
        if (!cashFlows || cashFlows.length === 0) return;

        renderCashFlowChart(cashFlows);
        renderDSCRChart(cashFlows);
        renderSubScoreRadar(subScores);
        renderCumulativeCFChart(cashFlows);
    };

    function renderCashFlowChart(data) {
        var ctx = document.getElementById("cashFlowChart");
        if (!ctx) return;

        var years = data.map(function (d) { return "Yr " + d.year; });
        var revenue = data.map(function (d) { return d.revenue; });
        var opex = data.map(function (d) { return d.opex; });
        var debtService = data.map(function (d) { return d.debt_service; });
        var freeCF = data.map(function (d) { return d.free_cash_flow; });

        new Chart(ctx, {
            type: "bar",
            data: {
                labels: years,
                datasets: [
                    {
                        label: "Revenue",
                        data: revenue,
                        backgroundColor: COLORS.blue,
                        order: 2
                    },
                    {
                        label: "Operating Expenses",
                        data: opex,
                        backgroundColor: COLORS.orange,
                        order: 2
                    },
                    {
                        label: "Debt Service",
                        data: debtService,
                        backgroundColor: COLORS.red,
                        order: 2
                    },
                    {
                        label: "Free Cash Flow",
                        type: "line",
                        data: freeCF,
                        borderColor: COLORS.secondary,
                        backgroundColor: COLORS.greenFill,
                        fill: false,
                        tension: 0.3,
                        pointRadius: 2,
                        order: 1
                    }
                ]
            },
            options: Object.assign({}, chartDefaults, {
                plugins: Object.assign({}, chartDefaults.plugins, {
                    title: { display: true, text: "Annual Cash Flow Waterfall", font: { size: 13 } }
                }),
                scales: {
                    y: {
                        ticks: {
                            callback: function (v) { return "$" + (v / 1e6).toFixed(1) + "M"; },
                            font: { size: 10 }
                        },
                        title: { display: true, text: "USD", font: { size: 11 } }
                    },
                    x: {
                        ticks: { font: { size: 10 }, maxRotation: 45 }
                    }
                }
            })
        });
    }

    function renderDSCRChart(data) {
        var ctx = document.getElementById("dscrChart");
        if (!ctx) return;

        var years = data.map(function (d) { return "Yr " + d.year; });
        var dscr = data.map(function (d) { return d.dscr; });

        new Chart(ctx, {
            type: "line",
            data: {
                labels: years,
                datasets: [
                    {
                        label: "DSCR",
                        data: dscr,
                        borderColor: COLORS.primary,
                        backgroundColor: COLORS.blueFill,
                        fill: true,
                        tension: 0.3,
                        pointRadius: 3
                    },
                    {
                        label: "Min Required (1.20x)",
                        data: years.map(function () { return 1.2; }),
                        borderColor: COLORS.danger,
                        borderDash: [6, 4],
                        pointRadius: 0,
                        fill: false
                    },
                    {
                        label: "Target (1.40x)",
                        data: years.map(function () { return 1.4; }),
                        borderColor: COLORS.accent,
                        borderDash: [4, 3],
                        pointRadius: 0,
                        fill: false
                    }
                ]
            },
            options: Object.assign({}, chartDefaults, {
                plugins: Object.assign({}, chartDefaults.plugins, {
                    title: { display: true, text: "Debt Service Coverage Ratio", font: { size: 13 } }
                }),
                scales: {
                    y: {
                        min: 0,
                        title: { display: true, text: "DSCR (x)", font: { size: 11 } },
                        ticks: { font: { size: 10 } }
                    },
                    x: {
                        ticks: { font: { size: 10 }, maxRotation: 45 }
                    }
                }
            })
        });
    }

    function renderSubScoreRadar(subScores) {
        var ctx = document.getElementById("subScoreRadar");
        if (!ctx || !subScores || subScores.length === 0) return;

        var labels = subScores.map(function (s) { return s.category; });
        var scores = subScores.map(function (s) { return s.score; });

        new Chart(ctx, {
            type: "radar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Score",
                    data: scores,
                    backgroundColor: COLORS.blueFill,
                    borderColor: COLORS.primary,
                    pointBackgroundColor: COLORS.primary,
                    pointRadius: 4
                }]
            },
            options: Object.assign({}, chartDefaults, {
                plugins: Object.assign({}, chartDefaults.plugins, {
                    title: { display: true, text: "Score Profile", font: { size: 13 } }
                }),
                scales: {
                    r: {
                        min: 0,
                        max: 100,
                        ticks: { stepSize: 20, font: { size: 10 } },
                        pointLabels: { font: { size: 11 } }
                    }
                }
            })
        });
    }

    function renderCumulativeCFChart(data) {
        var ctx = document.getElementById("cumulativeCFChart");
        if (!ctx) return;

        var years = data.map(function (d) { return "Yr " + d.year; });
        var cum = data.map(function (d) { return d.cumulative_cf; });

        new Chart(ctx, {
            type: "line",
            data: {
                labels: years,
                datasets: [{
                    label: "Cumulative Cash Flow",
                    data: cum,
                    borderColor: COLORS.secondary,
                    backgroundColor: COLORS.greenFill,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 2
                }]
            },
            options: Object.assign({}, chartDefaults, {
                plugins: Object.assign({}, chartDefaults.plugins, {
                    title: { display: true, text: "Cumulative Free Cash Flow", font: { size: 13 } }
                }),
                scales: {
                    y: {
                        ticks: {
                            callback: function (v) { return "$" + (v / 1e6).toFixed(1) + "M"; },
                            font: { size: 10 }
                        },
                        title: { display: true, text: "USD", font: { size: 11 } }
                    },
                    x: {
                        ticks: { font: { size: 10 }, maxRotation: 45 }
                    }
                }
            })
        });
    }

})();
