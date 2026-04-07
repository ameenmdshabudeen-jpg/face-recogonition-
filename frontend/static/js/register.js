document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("register-form");
    const video = document.getElementById("registration-video");
    const canvas = document.getElementById("registration-canvas");
    const preview = document.getElementById("capture-preview");
    const captureButton = document.getElementById("capture-button");
    const registerButton = document.getElementById("register-button");
    const statusBox = document.getElementById("register-status");
    const hiddenFaceImage = document.getElementById("face-image");
    const studentNameInput = document.getElementById("student-name");
    const studentRollNumberInput = document.getElementById("student-roll-number");
    const studentDepartmentInput = document.getElementById("student-department");

    let mediaStream = null;

    const setStatus = (message, tone = "info") => {
        statusBox.textContent = message;
        statusBox.className = `inline-status ${tone}`;
    };

    const stopCamera = () => {
        if (!mediaStream) {
            return;
        }

        mediaStream.getTracks().forEach((track) => track.stop());
        mediaStream = null;
    };

    const startCamera = async () => {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            setStatus("This browser does not support webcam capture.", "danger");
            return;
        }

        try {
            mediaStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: "user",
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                },
                audio: false
            });

            video.srcObject = mediaStream;
            setStatus("Camera ready. Capture one clear face to continue.", "success");
        } catch (error) {
            console.error(error);
            setStatus(
                "Unable to access the webcam. Check browser permissions or camera availability.",
                "danger"
            );
        }
    };

    const captureFrame = () => {
        if (!mediaStream || video.readyState < 2 || !video.videoWidth) {
            setStatus("The camera feed is not ready yet. Please wait a moment.", "warning");
            return;
        }

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const context = canvas.getContext("2d");
        // Capture the current webcam frame so the backend can build a face encoding from it.
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        const frame = canvas.toDataURL("image/jpeg", 0.92);
        hiddenFaceImage.value = frame;
        preview.src = frame;
        preview.classList.remove("hidden");
        setStatus("Face captured. Review the preview, then save the student.", "success");
    };

    const submitRegistration = async (event) => {
        event.preventDefault();

        const payload = {
            name: studentNameInput.value.trim(),
            roll_number: studentRollNumberInput.value.trim(),
            department: studentDepartmentInput.value.trim(),
            face_image: hiddenFaceImage.value
        };

        if (!payload.name || !payload.roll_number || !payload.department) {
            setStatus("Please complete all student details before saving.", "warning");
            return;
        }

        if (!payload.face_image) {
            setStatus("Please capture the student's face before saving.", "warning");
            return;
        }

        registerButton.disabled = true;
        registerButton.textContent = "Saving...";
        setStatus("Submitting student record to the server...", "info");

        try {
            const response = await fetch("/students", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Student registration failed.");
            }

            setStatus(data.message, "success");
            form.reset();
            hiddenFaceImage.value = "";
            preview.classList.add("hidden");
            preview.removeAttribute("src");

            window.setTimeout(() => {
                window.location.href = data.redirect_url || "/dashboard";
            }, 1000);
        } catch (error) {
            console.error(error);
            setStatus(error.message, "danger");
        } finally {
            registerButton.disabled = false;
            registerButton.textContent = "Save Student";
        }
    };

    captureButton.addEventListener("click", captureFrame);
    form.addEventListener("submit", submitRegistration);
    window.addEventListener("beforeunload", stopCamera);

    startCamera();
});
