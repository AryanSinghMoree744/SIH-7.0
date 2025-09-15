const video = document.getElementById('video');
const canvas = document.getElementById('overlay');
const statusText = document.getElementById('status');
let faceMatcher;
const recognizedStudents = new Set();

// Load face-api.js models
async function loadModels() {
    const MODEL_URL = '/static/models'; // you can serve models here
    await Promise.all([
        faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
        faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
        faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL)
    ]);
    statusText.innerText = '✅ Models loaded';
    startVideo();
}

// Start webcam
function startVideo() {
    navigator.mediaDevices.getUserMedia({ video: {} })
        .then(stream => video.srcObject = stream)
        .catch(err => statusText.innerText = 'Camera access denied.');
}

// Detect faces
video.addEventListener('play', () => {
    const displaySize = { width: video.width, height: video.height };
    faceapi.matchDimensions(canvas, displaySize);

    setInterval(async () => {
        const detections = await faceapi.detectAllFaces(video, new faceapi.TinyFaceDetectorOptions())
            .withFaceLandmarks()
            .withFaceDescriptors();

        const resized = faceapi.resizeResults(detections, displaySize);
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        for (let detection of resized) {
            const box = detection.detection.box;
            const label = "Unknown";
            new faceapi.draw.DrawBox(box, { label }).draw(canvas);

            // Send snapshot to backend for recognition
            const snapshot = canvas.toDataURL('image/jpeg');
            if (!recognizedStudents.has(snapshot)) {
                recognizedStudents.add(snapshot);
                fetch('/api/face_login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image: snapshot })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        statusText.innerText = `${data.name} ✅ Present`;
                        console.log('Attendance marked for', data.name);

                        // Optional: update charts dynamically
                        updateCharts(data.student_id);
                    } else {
                        statusText.innerText = 'Face not recognized';
                    }
                })
                .catch(err => console.error(err));
            }
        }

    }, 1000);
});

// Update charts dynamically
function updateCharts(student_id) {
    fetch(`/api/attendance_summary/${student_id}`)
    .then(res => res.json())
    .then(data => {
        // Example: update pie chart if using Chart.js
        if(window.attendancePieChart){
            window.attendancePieChart.data.datasets[0].data = data.values;
            window.attendancePieChart.update();
        }
    });
}

loadModels();
