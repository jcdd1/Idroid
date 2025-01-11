document.addEventListener("DOMContentLoaded", () => {
    const successAlert = document.querySelector(".alert-success");
    if (successAlert) {
        setTimeout(() => {
            successAlert.classList.add("fade-out");
            setTimeout(() => successAlert.remove(), 500);
        }, 5000);
    }
});
