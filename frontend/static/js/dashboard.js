document.addEventListener("DOMContentLoaded", () => {
    const retrainForm = document.getElementById("retrain-form");

    if (!retrainForm) {
        return;
    }

    retrainForm.addEventListener("submit", (event) => {
        const shouldContinue = window.confirm(
            "Retrain all stored face encodings from the saved registration images?"
        );

        if (!shouldContinue) {
            event.preventDefault();
            return;
        }

        const submitButton = retrainForm.querySelector("button[type='submit']");
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = "Retraining...";
        }
    });
});
