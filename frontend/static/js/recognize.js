document.addEventListener("DOMContentLoaded", () => {
    const video = document.getElementById("recognition-video");
    const overlayCanvas = document.getElementById("overlay-canvas");
    const frameCanvas = document.getElementById("frame-canvas");
    const statusBox = document.getElementById("recognition-status");
    const startButton = document.getElementById("start-scan-button");
    const stopButton = document.getElementById("stop-scan-button");
    const resultsContainer = document.getElementById("recognition-results");
    const attendanceEventsContainer = document.getElementById("attendance-events");

    let mediaStream = null;
    let intervalId = null;
    let isProcessing = false;
    const seenAttendanceIds = new Set();
    const eventHistory = [];

    const setStatus = (message, tone = "info") => {
        statusBox.textContent = message;
        statusBox.className = `inline-status ${tone}`;
    };

    const escapeHtml = (value) =>
        String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");

    const renderResults = (results) => {
        if (!results.length) {
            resultsContainer.innerHTML = `
                <div class="result-card placeholder-card">
                    No faces detected in the latest frame.
                </div>
            `;
            return;
        }

        resultsContainer.innerHTML = results
            .map((result) => {
                const attendanceStatus = result.attendance_status || "unknown";
                const displayRoll = result.roll_number || "Not registered";
                const displayDepartment = result.department || "Unknown";

                return `
                    <article class="result-card">
                        <h4>${escapeHtml(result.name)}</h4>
                        <div>${escapeHtml(displayRoll)} - ${escapeHtml(displayDepartment)}</div>
                        <div class="result-meta">
                            <span class="status-pill ${attendanceStatus}">
                                ${escapeHtml(attendanceStatus.replace(/_/g, " "))}
                            </span>
                            <span class="status-pill">
                                Confidence ${Number(result.confidence).toFixed(2)}%
                            </span>
                        </div>
                    </article>
                `;
            })
            .join("");
    };

    const renderEvents = () => {
        if (!eventHistory.length) {
            attendanceEventsContainer.innerHTML = `
                <div class="result-card placeholder-card">
                    Attendance confirmations will appear here.
                </div>
            `;
            return;
        }

        attendanceEventsContainer.innerHTML = eventHistory
            .map(
                (event) => `
                    <article class="result-card">
                        <h4>${escapeHtml(event.name)}</h4>
                        <div>${escapeHtml(event.roll_number)} - ${escapeHtml(event.department)}</div>
                        <div class="result-meta">
                            <span class="status-pill marked">
                                Marked ${escapeHtml(event.attendance_date)} ${escapeHtml(event.attendance_time)}
                            </span>
                        </div>
                    </article>
                `
            )
            .join("");
    };

    const drawOverlay = (results) => {
        const context = overlayCanvas.getContext("2d");
        const width = video.clientWidth;
        const height = video.clientHeight;

        overlayCanvas.width = width;
        overlayCanvas.height = height;
        context.clearRect(0, 0, width, height);

        if (!video.videoWidth || !results.length) {
            return;
        }

        const scaleX = width / video.videoWidth;
        const scaleY = height / video.videoHeight;

        results.forEach((result) => {
            const { top, right, bottom, left } = result.location;
            const x = left * scaleX;
            const y = top * scaleY;
            const boxWidth = (right - left) * scaleX;
            const boxHeight = (bottom - top) * scaleY;
            const isKnown = Boolean(result.student_id);

            context.strokeStyle = isKnown ? "#218380" : "#c1121f";
            context.lineWidth = 3;
            context.strokeRect(x, y, boxWidth, boxHeight);

            context.fillStyle = isKnown ? "#218380" : "#c1121f";
            context.fillRect(x, Math.max(y - 28, 0), Math.max(boxWidth, 120), 24);

            context.fillStyle = "#ffffff";
            context.font = "14px Segoe UI";
            context.fillText(result.name, x + 8, Math.max(y - 11, 15));
        });
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
            setStatus("This browser does not support webcam access.", "danger");
            return false;
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
            setStatus("Camera ready. Live scanning is active.", "success");
            return true;
        } catch (error) {
            console.error(error);
            setStatus(
                "Unable to access the webcam. Check browser permissions or camera availability.",
                "danger"
            );
            return false;
        }
    };

    const scanFrame = async () => {
        if (isProcessing || !mediaStream || video.readyState < 2 || !video.videoWidth) {
            return;
        }

        isProcessing = true;

        try {
            frameCanvas.width = video.videoWidth;
            frameCanvas.height = video.videoHeight;

            const context = frameCanvas.getContext("2d");
            // Each scan sends a compressed frame to the backend for multi-face recognition.
            context.drawImage(video, 0, 0, frameCanvas.width, frameCanvas.height);

            const frame = frameCanvas.toDataURL("image/jpeg", 0.72);
            const response = await fetch("/api/recognize", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ frame })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Recognition failed.");
            }

            renderResults(data.results || []);
            drawOverlay(data.results || []);

            (data.attendance_events || []).forEach((event) => {
                if (seenAttendanceIds.has(event.id)) {
                    return;
                }

                seenAttendanceIds.add(event.id);
                eventHistory.unshift(event);
            });

            eventHistory.splice(8);
            renderEvents();

            if (!data.results || data.results.length === 0) {
                setStatus("No faces detected in the current frame.", "warning");
            } else {
                setStatus(`Processed ${data.results.length} face(s) at ${data.processed_at}.`, "success");
            }
        } catch (error) {
            console.error(error);
            setStatus(error.message, "danger");
        } finally {
            isProcessing = false;
        }
    };

    const startScanning = async () => {
        if (!mediaStream) {
            const ready = await startCamera();
            if (!ready) {
                return;
            }
        }

        if (intervalId) {
            return;
        }

        intervalId = window.setInterval(scanFrame, 1400);
        setStatus("Live scanning is running.", "success");
    };

    const stopScanning = () => {
        if (intervalId) {
            window.clearInterval(intervalId);
            intervalId = null;
        }

        const context = overlayCanvas.getContext("2d");
        context.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
        setStatus("Scanning paused. The camera feed is still available.", "warning");
    };

    startButton.addEventListener("click", startScanning);
    stopButton.addEventListener("click", stopScanning);

    window.addEventListener("beforeunload", () => {
        stopScanning();
        stopCamera();
    });

    startScanning();
});
