
document.addEventListener("DOMContentLoaded", function () {
    console.log("LUMIERA cart JS loaded");

    document.querySelectorAll(".quantity-control").forEach(function (control) {
        const input = control.querySelector('input[name="quantity"]');
        const minus = control.querySelector(".quantity-minus");
        const plus = control.querySelector(".quantity-plus");

        if (!input || !minus || !plus) {
            console.error("Quantity elements missing", control);
            return;
        }

        minus.addEventListener("click", function () {
            const min = Number(input.min) || 1;
            const current = Number(input.value) || min;
            input.value = Math.max(min, current - 1);
            input.dispatchEvent(new Event("change", { bubbles: true }));
            console.log("Minus clicked:", input.value);
        });

        plus.addEventListener("click", function () {
            const min = Number(input.min) || 1;
            const max = input.max ? Number(input.max) : Infinity;
            const current = Number(input.value) || min;
            input.value = Math.min(max, current + 1);
            input.dispatchEvent(new Event("change", { bubbles: true }));
            console.log("Plus clicked:", input.value);
        });
    });
});