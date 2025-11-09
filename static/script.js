let exampleFile = null;
let assignmentFile = null;

// DOM Elements
const exampleInput = document.getElementById('example-input');
const assignmentInput = document.getElementById('assignment-input');
const exampleName = document.getElementById('example-name');
const assignmentName = document.getElementById('assignment-name');
const compareBtn = document.getElementById('compare-btn');
const studentNameInput = document.getElementById('student-name');
const focusAreasSelect = document.getElementById('focus-areas');

const uploadSection = document.getElementById('upload-section');
const progressSection = document.getElementById('progress-section');
const resultsSection = document.getElementById('results-section');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');

const newComparisonBtn = document.getElementById('new-comparison-btn');
const loadReportsBtn = document.getElementById('load-reports-btn');
const reportsList = document.getElementById('reports-list');

// File selection
exampleInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        exampleFile = file;
        exampleName.textContent = `✓ ${file.name}`;
        checkReadyToCompare();
    }
});

assignmentInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        assignmentFile = file;
        assignmentName.textContent = `✓ ${file.name}`;
        checkReadyToCompare();
    }
});

function checkReadyToCompare() {
    compareBtn.disabled = !(exampleFile && assignmentFile);
}

// Compare videos
compareBtn.addEventListener('click', async () => {
    if (!exampleFile || !assignmentFile) return;

    uploadSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    progressSection.classList.remove('hidden');

    try {
        // Step 1: Upload example video
        updateProgress(10, 'Uploading example video...');
        await uploadFile(exampleFile, 'example');

        // Step 2: Upload assignment video
        updateProgress(30, 'Uploading assignment video...');
        await uploadFile(assignmentFile, 'assignment');

        // Step 3: Extract poses and compare
        updateProgress(50, 'Analyzing choreography...');

        const studentName = studentNameInput.value || 'Student';
        const focusAreas = Array.from(focusAreasSelect.selectedOptions)
            .map(opt => opt.value)
            .join(',');

        const result = await compareVideos(
            exampleFile.name,
            assignmentFile.name,
            focusAreas,
            studentName
        );

        // Step 4: Display results
        updateProgress(100, 'Complete!');

        setTimeout(() => {
            progressSection.classList.add('hidden');
            displayResults(result);
        }, 500);

    } catch (error) {
        console.error('Error during comparison:', error);
        alert('Error processing videos. Please try again.');
        updateProgress(0, 'Error occurred');
        progressSection.classList.add('hidden');
        uploadSection.classList.remove('hidden');
    }
});

// Upload file
async function uploadFile(file, type) {
    const formData = new FormData();
    formData.append('file', file);

    const endpoint = type === 'example' ? '/upload-example' : '/upload-assignment';

    const response = await fetch(endpoint, {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
    }

    return await response.json();
}

// Compare videos
async function compareVideos(exampleFilename, assignmentFilename, focusAreas, studentName) {
    const params = new URLSearchParams({
        example_filename: exampleFilename,
        assignment_filename: assignmentFilename,
        student_name: studentName
    });

    if (focusAreas) {
        params.append('focus_areas', focusAreas);
    }

    const response = await fetch(`/compare?${params.toString()}`, {
        method: 'POST'
    });

    if (!response.ok) {
        throw new Error(`Comparison failed: ${response.statusText}`);
    }

    return await response.json();
}

// Update progress
function updateProgress(percent, text) {
    progressFill.style.width = `${percent}%`;
    progressText.textContent = text;
}

// Display results
function displayResults(result) {
    // Overall score
    const overallScore = result.overall_similarity;
    document.getElementById('overall-score').textContent = `${overallScore}%`;

    // Set color based on score
    const scoreCircle = document.getElementById('overall-score');
    if (overallScore >= 80) {
        scoreCircle.style.background = 'linear-gradient(135deg, #CFB991, #B1810B)';
    } else if (overallScore >= 65) {
        scoreCircle.style.background = 'linear-gradient(135deg, #B1810B, #8B6508)';
    } else {
        scoreCircle.style.background = 'linear-gradient(135deg, #1c1c1c, #000000)';
    }

    // Breakdown scores
    const breakdown = result.similarity_breakdown;

    animateScore('pose-score', 'pose-value', breakdown.pose_accuracy);
    animateScore('timing-score', 'timing-value', breakdown.timing_accuracy);
    animateScore('smoothness-score', 'smoothness-value', breakdown.movement_smoothness);
    animateScore('angle-score', 'angle-value', breakdown.angle_accuracy);

    // AI Feedback
    document.getElementById('ai-feedback').textContent = result.ai_feedback;

    // Feedback points
    const feedbackPoints = result.feedback_points;
    const feedbackContainer = document.getElementById('feedback-points');
    feedbackContainer.innerHTML = '';

    feedbackPoints.forEach(point => {
        const pointDiv = document.createElement('div');
        pointDiv.className = `feedback-point ${point.severity}`;

        pointDiv.innerHTML = `
            <div class="feedback-point-header">
                <span class="feedback-timestamp">${point.timestamp}</span>
                <span class="feedback-severity ${point.severity}">${point.severity.toUpperCase()}</span>
            </div>
            <div class="feedback-issue">${point.issue}</div>
            <div class="feedback-suggestion">${point.suggestion}</div>
        `;

        feedbackContainer.appendChild(pointDiv);
    });

    // Show results
    resultsSection.classList.remove('hidden');
}

function animateScore(barId, valueId, score) {
    const bar = document.getElementById(barId);
    const value = document.getElementById(valueId);

    setTimeout(() => {
        bar.style.width = `${score}%`;
        value.textContent = `${score}%`;
    }, 100);
}

// New comparison
newComparisonBtn.addEventListener('click', () => {
    resultsSection.classList.add('hidden');
    uploadSection.classList.remove('hidden');

    // Reset form
    exampleFile = null;
    assignmentFile = null;
    exampleName.textContent = '';
    assignmentName.textContent = '';
    exampleInput.value = '';
    assignmentInput.value = '';
    compareBtn.disabled = true;
});

// Load reports
loadReportsBtn.addEventListener('click', async () => {
    try {
        const response = await fetch('/reports');
        const data = await response.json();

        reportsList.innerHTML = '';

        if (data.reports.length === 0) {
            reportsList.innerHTML = '<p style="color: #6c757d;">No reports found.</p>';
        } else {
            data.reports.forEach(report => {
                const reportDiv = document.createElement('div');
                reportDiv.className = 'report-item';

                const date = new Date(report.timestamp).toLocaleString();

                reportDiv.innerHTML = `
                    <div class="report-info">
                        <div class="report-name">${report.student_name}</div>
                        <div class="report-date">${date}</div>
                    </div>
                    <div class="report-score">${report.overall_similarity}%</div>
                    <div class="report-actions">
                        <button class="btn btn-secondary btn-small" onclick="viewReport('${report.filename}')">
                            View
                        </button>
                        <button class="btn btn-secondary btn-small" onclick="deleteReport('${report.filename}')">
                            Delete
                        </button>
                    </div>
                `;

                reportsList.appendChild(reportDiv);
            });
        }

        reportsList.classList.remove('hidden');

    } catch (error) {
        console.error('Error loading reports:', error);
        alert('Error loading reports.');
    }
});

async function viewReport(filename) {
    try {
        const response = await fetch(`/reports/${filename}`);
        const result = await response.json();

        uploadSection.classList.add('hidden');
        progressSection.classList.add('hidden');
        displayResults(result);

    } catch (error) {
        console.error('Error loading report:', error);
        alert('Error loading report.');
    }
}

async function deleteReport(filename) {
    if (!confirm('Are you sure you want to delete this report?')) {
        return;
    }

    try {
        await fetch(`/reports/${filename}`, { method: 'DELETE' });
        loadReportsBtn.click(); // Reload reports list

    } catch (error) {
        console.error('Error deleting report:', error);
        alert('Error deleting report.');
    }
}
